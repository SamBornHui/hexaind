from __future__ import annotations

from collections import defaultdict
from enum import Enum, auto
from functools import cached_property
from hashlib import md5
from itertools import groupby
from math import inf
from operator import itemgetter
from pathlib import Path
from typing import (
    Annotated,
    Any,
    ClassVar,
    DefaultDict,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
)
from uuid import uuid4

import polars as pl
from pydantic import (
    BaseModel,
    DirectoryPath,
    Field,
    FilePath,
    PositiveInt,
    RootModel,
    field_validator,
)

from app.config.env_vars import environment


class SelectionOperation(str, Enum):

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    ALL = auto()
    QUERY = auto()
    MANUAL = auto()


class AllSection(BaseModel):
    operation: Literal[SelectionOperation.ALL]


class QuerySelection(BaseModel):
    operation: Literal[SelectionOperation.QUERY]
    query: str
    regex: bool = False


class ManualSelection(BaseModel):
    operation: Literal[SelectionOperation.MANUAL]
    values: List[Any]


class Selection(RootModel):
    root: Annotated[
        Union[
            AllSection,
            QuerySelection,
            ManualSelection,
        ],
        Field(discriminator="operation"),
    ]


class FilterOperand(str, Enum):

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    AND = auto()
    OR = auto()
    XOR = auto()


class FilterOperation(str, Enum):

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    EQ = auto()  # equal
    NE = auto()  # not equal
    BW = auto()  # between
    LQ = auto()  # like
    NLQ = auto()  # not like


class EqualFilter(BaseModel):
    operation: Literal[FilterOperation.EQ]
    value: Union[List[Any], Any]


class NotEqualFilter(BaseModel):
    operation: Literal[FilterOperation.NE]
    value: Union[List[Any], Any]


class BetweenFilter(BaseModel):
    operation: Literal[FilterOperation.BW]
    value: Tuple[Any, Any]


class LikeFilter(BaseModel):
    operation: Literal[FilterOperation.LQ]
    value: str
    regex: bool = False


class NotLikeFilter(BaseModel):
    operation: Literal[FilterOperation.NLQ]
    value: str
    regex: bool = False


class Filter(RootModel):
    root: Annotated[
        Union[
            EqualFilter,
            NotEqualFilter,
            BetweenFilter,
            LikeFilter,
            NotLikeFilter,
        ],
        Field(discriminator="operation"),
    ]


class PathRequest(BaseModel):
    path: Union[FilePath, DirectoryPath] = Field(
        description="file path of parquet dataset"
    )

    @cached_property
    def raw_lazyframe(self) -> pl.LazyFrame:
        # assuming data is in parquet format
        lf = pl.scan_parquet(source=self.path)
        return lf.with_columns(pl.int_range(pl.len(), dtype=pl.UInt32).alias("index"))

    def rows(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return lf.select(pl.len())

    def columns(self, lf: pl.LazyFrame) -> Set[str]:
        return set(lf.collect_schema().names())


class PaginatedRequest(BaseModel):
    page_number: PositiveInt = Field(description="page number", default=1)
    page_size: PositiveInt = Field(description="page limit", default=100)
    ignore_pagination: bool = Field(
        description="ignores pagination and sends entire data frame", default=False
    )

    def paginated_lazyframe(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        if self.ignore_pagination:
            return lf
        return lf.slice(
            offset=(self.page_number - 1) * self.page_size,
            length=self.page_size,
        )


class FilterRequest(BaseModel):
    filters: List[Tuple[str, Filter, FilterOperand]] = Field(
        description="filters to apply", default_factory=list
    )

    @field_validator("filters", mode="before")
    @classmethod
    def update_filters(
        cls, filters: Union[Dict[str, Filter], List[Tuple[str, Filter, FilterOperand]]]
    ) -> List[Tuple[str, Filter, FilterOperand]]:
        if isinstance(filters, dict):
            return [
                (column, filter_, FilterOperand.AND)
                for column, filter_ in filters.items()
            ]
        return filters

    @cached_property
    def predicates(self) -> List[Tuple[str, pl.Expr]]:
        result = []
        for column, group in groupby(
            sorted(self.filters, key=itemgetter(0), reverse=True), key=itemgetter(0)
        ):
            aggregated_predicate: Optional[pl.Expr] = None
            for _, filter_, operand in group:
                match filter_.root:
                    case EqualFilter(value=value) if isinstance(value, list):
                        predicate = pl.col(column).is_in(value)
                    case EqualFilter(value=value):
                        predicate = pl.col(column).eq(value)
                    case NotEqualFilter(value=value) if isinstance(value, list):
                        predicate = pl.col(column).is_in(value).not_()
                    case BetweenFilter(value=value):
                        lower_bound, upper_bound = map(pl.lit, value)
                        predicate = pl.col(column).is_between(lower_bound, upper_bound)
                    case LikeFilter(value=value, regex=regex):
                        predicate = pl.col(column).str.contains(
                            value, literal=not regex
                        )
                    case NotLikeFilter(value=value, regex=regex):
                        predicate = (
                            pl.col(column).str.contains(value, literal=not regex).not_()
                        )
                    case _:
                        continue
                if aggregated_predicate is None:
                    aggregated_predicate = predicate
                else:
                    match operand:
                        case FilterOperand.AND:
                            aggregated_predicate &= predicate
                        case FilterOperand.OR:
                            aggregated_predicate |= predicate
                        case FilterOperand.XOR:
                            aggregated_predicate ^= predicate
                        case _:
                            continue
            if aggregated_predicate is None:
                continue
            result.append((column, aggregated_predicate))
        return result

    def filtered_lazyframe(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        for _, predicate in self.predicates:
            lf = lf.filter(predicate)
        return lf


class DataQueryRequest(PaginatedRequest, FilterRequest, PathRequest):
    included_columns: Set[str] = Field(
        description="columns to include", default_factory=set
    )
    excluded_columns: Set[str] = Field(
        description="columns to exclude", default_factory=set
    )
    save: bool = Field(description="flag to save the filtered data", default=False)
    is_unique: bool = Field(description="get only unique values", default=False)
    do_not_send_data: bool = Field(
        description="keep this true when wanting to save the files instead of showing",
        default=False,
    )

    def columns(self, lf: pl.LazyFrame) -> Set[str]:
        if not self.included_columns:
            self.included_columns = super().columns(lf)
        return self.included_columns - self.excluded_columns

    def uniques(self, lf: pl.LazyFrame) -> Generator[pl.LazyFrame, None, None]:
        for column in self.columns(lf):
            predicates = [
                predicate
                for filter_column, predicate in self.predicates
                if filter_column != column
            ]
            if predicates:
                lf = lf.filter(*predicates)
            yield lf.select(column).unique(column).sort(by=column).drop_nulls(column)

    @cached_property
    def lazyframe(self) -> pl.LazyFrame:
        return self.filtered_lazyframe(self.raw_lazyframe).select(
            list(self.columns(self.raw_lazyframe))
        )

    def __hash__(self) -> int:
        return int(md5(repr(self).encode()).hexdigest(), base=16)


class DataQueryResponse(BaseModel):
    columns: List[str] = Field(description="names of the selected columns")
    data: List[Dict[str, Any]] = Field(description="tabular data in records format")
    uniques: Dict[str, List[Any]] = Field(description="unique values for the columns")
    rows_count: int = Field(description="total number of columns")
    saved_path: Optional[Path] = Field(description="saved path", default=None)

    columns_order: ClassVar[DefaultDict] = defaultdict(
        lambda: inf,
        {
            name: i
            for i, name in enumerate(
                [
                    "DWH_SRCID",
                    "DESIGN_ID",
                    "RECIPE_NAME",
                    "TOOL_NAME",
                    "TOOL_ID",
                    "RUN_ID",
                    "LOT_ID",
                    "WAFER_ID",
                    "TRAVELER_STEP",
                    "START_DATE",
                ]
            )
        },
    )

    @classmethod
    def from_data_query(cls, query: DataQueryRequest) -> DataQueryResponse:
        df, rows_count, *uniques = pl.collect_all(
            [
                query.paginated_lazyframe(
                    query.lazyframe.unique() if query.is_unique else query.lazyframe
                ),
                query.rows(query.lazyframe),
                *query.uniques(query.lazyframe),
            ]
        )

        saved_path: Optional[Path] = None
        if query.save:
            saved_path = (
                environment.hexaind_data / "micron_cache" / f"{hash(query)}.parquet"
            )
            saved_path.parent.mkdir(parents=True, exist_ok=True)
            query.filtered_lazyframe(query.raw_lazyframe).collect().write_parquet(
                saved_path
            )

        columns = query.columns(query.lazyframe)

        return cls(
            columns=sorted((columns - {"index"}), key=cls.columns_order.__getitem__),
            data=df.to_dicts() if not query.do_not_send_data else [],
            uniques={
                column: dataframe.to_dict(as_series=False)[column]
                for column, dataframe in zip(columns, uniques)
            },
            rows_count=rows_count.item(),
            saved_path=saved_path,
        )


class UniquesQueryRequest(PaginatedRequest, FilterRequest, PathRequest):
    column: str

    @cached_property
    def lazyframe(self) -> pl.LazyFrame:
        return (
            self.filtered_lazyframe(self.raw_lazyframe)
            .select(self.column)
            .unique(self.column)
            .sort(by=self.column)
            .drop_nulls(self.column)
        )


class UniquesQueryResponse(BaseModel):
    uniques: List[Any] = Field(description="uniques of the selected column")
    rows_count: int = Field(description="total number of columns")

    @classmethod
    def from_uniques_query(cls, query: UniquesQueryRequest) -> UniquesQueryResponse:
        df, rows_count = pl.collect_all(
            [
                query.paginated_lazyframe(query.lazyframe),
                query.rows(query.lazyframe),
            ]
        )
        uniques = df.to_dict(as_series=False)[query.column]
        return cls(
            uniques=uniques,
            rows_count=rows_count.item(),
        )


class SelectionQueryRequest(FilterRequest, PathRequest):
    column: str
    selection: Selection
    selected_path: Optional[FilePath] = None

    @cached_property
    def selection_predicate(self) -> pl.Expr:
        match self.selection.root:
            case AllSection():
                return pl.col(self.column) == pl.col(self.column)
            case QuerySelection(query=query, regex=regex):
                return pl.col(self.column).str.contains(query, literal=not regex)
            case ManualSelection(values=values):
                return pl.col(self.column).is_in(values)


class SelectionQueryResponse(BaseModel):
    selected_path: FilePath

    @staticmethod
    def generate_unique_file_path() -> Path:
        path = environment.hexaind_data / "micron_selection" / f"{uuid4().hex}.parquet"
        path.parent.mkdir(exist_ok=True, parents=True)
        return path

    @classmethod
    def from_unselection_query(
        cls, query: SelectionQueryRequest
    ) -> SelectionQueryResponse:
        if query.selected_path is None:
            lf = query.raw_lazyframe.slice(0, 0)
        else:
            lf = pl.scan_parquet(query.selected_path)
        selected_path = cls.generate_unique_file_path()
        (
            lf.filter(query.selection_predicate.not_())
            .collect()
            .write_parquet(selected_path)
        )
        return cls(selected_path=selected_path)

    @classmethod
    def from_selection_query(
        cls, query: SelectionQueryRequest
    ) -> SelectionQueryResponse:
        if query.selected_path is None:
            lf = query.raw_lazyframe.slice(0, 0)
        else:
            lf = pl.scan_parquet(query.selected_path)
        selected_path = cls.generate_unique_file_path()
        pl.concat(
            items=[
                lf,
                (
                    query.filtered_lazyframe(query.raw_lazyframe).filter(
                        query.selection_predicate
                    )
                ),
            ],
            how="vertical",
        ).unique(query.column).collect().write_parquet(selected_path)
        return cls(selected_path=selected_path)
