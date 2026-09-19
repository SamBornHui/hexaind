import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple

from dateutil.relativedelta import relativedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.dag_templates.wf_schedule_dag import generate_dag_file
from app.dag_templates.wf_trigger_dag import generate_dag_file as fb_dag
from app.services.workflows.runner.schemas import RunStatus
from app.services.workflows.scheduling.dao import ScheduleDao
from app.services.workflows.scheduling.schemas import (
    RepeatType,
    ScheduleType,
    SchedulingEventType,
    WFSchedule,
    WfScheduleInfo,
)
from app.services.workflows.scheduling.utils import (
    fetch_dag_next_run,
    get_job_trigger_datetimes,
    get_next_job_time,
    get_prev_weekday_date,
    pause_dag,
)

logger = logging.getLogger(__package__)


class ScheduleService:

    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:

        self.schedule_dao = ScheduleDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    def get_schedules_with_workflow(
        self, workflow_id: str, current_run_status: RunStatus
    ) -> List[WFSchedule]:
        schedules = self.schedule_dao.get_schedules_triggered_by(workflow_id)
        schedules_to_be_triggered = []
        for schedule in schedules:
            if schedule.event_based_config.config.condition == current_run_status:
                schedules_to_be_triggered.append(schedule)
        return schedules_to_be_triggered

    async def create_schedule(
        self, tags: List[str], token: str, wf_schedule: WFSchedule
    ):
        logger.info(
            f"Inside create_schedule function, creating new schedule with wf_id {wf_schedule.workflow_id}"
        )
        wf_schedule.job_trigger_dt_times = [wf_schedule.start_date]
        if wf_schedule.schedule_type == ScheduleType.RECURRING:
            date_format = "%Y-%m-%d %H:%M:%S"
            st_dt = datetime.strptime(wf_schedule.start_date, date_format)
            if wf_schedule.repeat_type == RepeatType.DAYS:
                wf_schedule.start_date = str(st_dt - timedelta(days=1))
                wf_schedule.scheduled_interval = f"{st_dt.minute} {st_dt.hour} * * *"
            if wf_schedule.repeat_type == RepeatType.WEEKS:
                cron_list_int = [
                    cron_day.value for cron_day in wf_schedule.cron_week_days
                ]
                cron_wk_day_val = min(cron_list_int)

                if wf_schedule.repeat_value == 1:
                    cron_wk_days = ",".join(map(str, cron_list_int))
                else:
                    cron_wk_days = str(cron_wk_day_val)

                prev_wd_matching_dt = get_prev_weekday_date(st_dt, cron_wk_day_val)
                wf_schedule.start_date = str(prev_wd_matching_dt)
                wf_schedule.scheduled_interval = (
                    f"{st_dt.minute} {st_dt.hour} * * {cron_wk_days}"
                )

            if wf_schedule.repeat_type == RepeatType.MONTHS:
                wf_schedule.start_date = str(st_dt - relativedelta(months=1))
                wf_schedule.scheduled_interval = (
                    f"{st_dt.minute} {st_dt.hour} {st_dt.day} * *"
                )
            if wf_schedule.repeat_type == RepeatType.YEARS:
                wf_schedule.start_date = str(st_dt - relativedelta(year=1))
                wf_schedule.scheduled_interval = (
                    f"{st_dt.minute} {st_dt.hour} {st_dt.day} {st_dt.month} *"
                )

            wf_schedule.job_trigger_dt_times = get_job_trigger_datetimes(wf_schedule)

        schedule_id = await self.schedule_dao.create_schedule_async(
            schedule=wf_schedule
        )
        if (
            wf_schedule.event_based_config
            and wf_schedule.event_based_config.event_type
            == SchedulingEventType.WF_COMPLETION_VIA_SCHEDULE_TRIGGER_WF
        ):
            return schedule_id

        elif (
            wf_schedule.event_based_config
            and wf_schedule.event_based_config.event_type
            == SchedulingEventType.ANY_FILE_IN_FOLDER_TRIGGER_WF
        ):
            generate_dag_file(
                dag_id=schedule_id,
                site_id=wf_schedule.site_id,
                workflow_id=wf_schedule.workflow_id,
                project_id=wf_schedule.project_id,
                token=token,
                start_date_input=wf_schedule.start_date,
                end_date_input=wf_schedule.end_date,
                schedule_interval_minutes=None,
                tags=tags,
                task_name=wf_schedule.name.strip().replace(" ", "_"),
                repeat_type=wf_schedule.repeat_type,
                repeat_value=wf_schedule.repeat_value,
            )

            dag_path = fb_dag(
                dag_id=f"trigger_{schedule_id}",
                site_id=wf_schedule.site_id,
                workflow_id=wf_schedule.workflow_id,
                workflow_dag_id=schedule_id,
                project_id=wf_schedule.project_id,
                start_date_input=wf_schedule.start_date,
                end_date_input=wf_schedule.end_date,
                schedule_interval_minutes=wf_schedule.scheduled_interval,
                tags=tags,
                path=Path(wf_schedule.event_based_config.config.folder_path),
            )

        else:
            dag_path = generate_dag_file(
                dag_id=schedule_id,
                site_id=wf_schedule.site_id,
                workflow_id=wf_schedule.workflow_id,
                project_id=wf_schedule.project_id,
                token=token,
                start_date_input=wf_schedule.start_date,
                end_date_input=wf_schedule.end_date,
                schedule_interval_minutes=wf_schedule.scheduled_interval,
                tags=tags,
                task_name=wf_schedule.name,
                repeat_type=wf_schedule.repeat_type,
                repeat_value=wf_schedule.repeat_value,
            )

        await self.schedule_dao.update_file_path_async(
            schedule_id=schedule_id, dag_path=dag_path
        )

        return schedule_id

    async def pause_dag(
        self, schedule_id: str, last_modified_id: str, is_paused: bool = True
    ):
        logger.info("Inside pause_dag function")
        json_response = pause_dag(dag_id=schedule_id, is_paused=is_paused)

        return await self.schedule_dao.update_is_active_async(
            schedule_id=schedule_id,
            last_modified_id=last_modified_id,
            is_paused=json_response["is_paused"],
        )

    async def delete_schedule(self, schedule_id: str):
        logger.info("Inside delete_schedule function")
        schedule_record = await self.schedule_dao.get_schedule_by_id_async(
            schedule_id=schedule_id
        )
        if (
            schedule_record.event_based_config
            and schedule_record.event_based_config.event_type
            == SchedulingEventType.WF_COMPLETION_VIA_SCHEDULE_TRIGGER_WF
        ):
            await self.schedule_dao.delete_schedule_async(schedule_id=schedule_id)
        else:
            dag_path = Path(schedule_record.dag_file_path)
            resp = pause_dag(dag_id=schedule_id, is_paused=True)

            if resp["is_paused"]:
                result = await self.schedule_dao.delete_schedule_async(
                    schedule_id=schedule_id
                )
                if dag_path.exists():
                    dag_path.unlink()
            else:
                logger.error("Failed to delete the schedule ..as dag is not paused")
                raise Exception("Failed to delete the schedule ..as dag is not paused")

    async def fetch_all_schedules_async(
        self,
        project_id: str,
        search_term: str = "",
        page_number: int = 1,
        page_limit: int = 100,
    ) -> Tuple[List[WFSchedule], int]:

        return await self.schedule_dao.get_all_schedule_async(
            project_id=project_id,
            search_term=search_term,
            page_number=page_number,
            page_limit=page_limit,
        )

    async def fetch_schedule_by_id_async(self, schedule_id: str) -> WFSchedule:

        return await self.schedule_dao.get_schedule_by_id_async(schedule_id=schedule_id)

    async def fetch_schedules_by_workflow_id_async(
        self, workflow_id: str
    ) -> List[WFSchedule]:

        return await self.schedule_dao.get_schedule_by_workflow_id_async(
            workflow_id=workflow_id
        )

    async def fetch_all_schedules_with_details_async(
        self,
        project_id: str,
        search_term: str = "",
        page_number: int = 1,
        page_limit: int = 1000,
        max_runs_fetch_limit: int = 5,
    ) -> Tuple[List[WfScheduleInfo], int]:
        logger.info("Inside fetch_all_schedules_with_details_async function")
        schedules, count = (
            await self.schedule_dao.get_schedule_with_runs_and_workflows_async(
                project_id=project_id,
                search_term=search_term,
                page_number=page_number,
                page_limit=page_limit,
                max_runs_fetch_limit=max_runs_fetch_limit,
            )
        )

        for schedule in schedules:
            schedule.next_run = "Unknown"

            if len(schedule.job_trigger_dt_times) == 0:
                schedule.job_trigger_dt_times = [schedule.start_date]

                if schedule.schedule_type == ScheduleType.RECURRING:
                    schedule.job_trigger_dt_times = get_job_trigger_datetimes(schedule)

            schedule.next_run = get_next_job_time(schedule.job_trigger_dt_times)

        # next_dag_run_result = {}
        # for dag_id in list(set([res.dag_id for res in schedules])):
        #     try:
        #         next_dag_run_result[dag_id] = fetch_dag_next_run(dag_id)
        #     except Exception as e:
        #         logger.error(f"unable to fetch next dag run {e}")
        #         logger.exception(f"unable to fetch next dag run {e}")

        # # populates next run value
        # for schedule in schedules:
        #     schedule.next_run = next_dag_run_result.get(
        #         schedule.dag_id, {"next_dagrun": "Unknown"}
        #     ).get("next_dagrun")

        return schedules, count
