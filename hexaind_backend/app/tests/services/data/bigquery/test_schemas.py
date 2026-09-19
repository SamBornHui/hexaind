import pytest
import pytest_mock
import pytest_asyncio

from app.services.data.bigquery.schemas import SchemaFieldType


@pytest.mark.asyncio
def test_schema_field_type_numeric():
    # Arrange
    bg_field_type = "INT64"

    # Act
    result = SchemaFieldType.from_bigquery_type(bg_field_type)

    # Assert
    assert result == SchemaFieldType.NUMERIC

@pytest.mark.asyncio
def test_schema_field_type_categorical():
    # Arrange
    bg_field_type = "STRING"

    # Act
    result = SchemaFieldType.from_bigquery_type(bg_field_type)

    # Assert
    assert result == SchemaFieldType.CATEGORICAL

@pytest.mark.asyncio
def test_schema_field_type_numeric_synonyms():
    # Arrange
    numeric_synonyms = ["FLOAT", "FLOAT64", "NUMERIC"]

    for bg_field_type in numeric_synonyms:
        # Act
        result = SchemaFieldType.from_bigquery_type(bg_field_type)

        # Assert
        assert result == SchemaFieldType.NUMERIC

@pytest.mark.asyncio
def test_schema_field_type_invalid_type():

    invalid_type = "INVALID_TYPE"
    result = SchemaFieldType.from_bigquery_type(invalid_type)
    assert result == SchemaFieldType.CATEGORICAL
