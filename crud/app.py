from datetime import datetime

from sqlmodel import select
from starlette.requests import Request

from api.deps import SessionDep
from common.execptions import validate_request_exception
from models import User
from models.app import AppSelect, App, AppCreate, AppDelete, AppReview


def get_passed_app(session: SessionDep, se: AppSelect):
    """
    获取所有 "已过审" "未删除" APP 供预览
    :param session:
    :param page_info:
    :return:
    """
    page_size = se.pageSize

    validate_request_exception(page_size > 20, '一次仅允许访问不超过20条数据')

    # 找符合条件的 app
    statement = select(App).where(App.review_status == 1).where(App.is_delete == 0)
    app_objs = session.exec(statement).all()

    # 处理数据，返回
    records = []
    for app in app_objs:
        user_id = app.user_id
        app_dict = app.to_dict()

        # 查询 User 信息
        user_sql = select(User).where(User.id == user_id)
        user_obj = session.exec(user_sql).first()
        if user_obj:
            app_dict['user'] = user_obj.to_dict()

        records.append(app_dict)
    return records


def get_all_app(session: SessionDep, se: AppSelect):
    page_size = se.pageSize

    validate_request_exception(page_size > 20, '一次仅允许访问不超过20条数据')

    # 找出所以app
    statement = select(App).where(App.is_delete == 0)
    if se.appName:
        statement = statement.where(App.app_name.like('%{}%'.format(se.appName)))
    if se.appDesc:
        statement = statement.where(App.app_desc.like('%{}%'.format(se.appDesc)))
    app_objs = session.exec(statement).all()

    # 处理数据，返回
    records = []
    for app in app_objs:
        user_id = app.user_id
        app_dict = app.to_dict()

        # 查询 User 信息
        user_sql = select(User).where(User.id == user_id)
        user_obj = session.exec(user_sql).first()
        if user_obj:
            app_dict['user'] = user_obj.to_dict()

        records.append(app_dict)
    return records


def delete_app_by_id(session: SessionDep, app_del: AppDelete):
    """
    通过 id 删除 APP
    :param session:
    :param app_del:
    :return:
    """
    app_id = app_del.id
    sql = select(App).where(App.id == app_id)
    app_obj = session.exec(sql).first()
    validate_request_exception(not app_obj, '应用不存在')

    app_obj.is_delete = 1
    session.commit()
    session.refresh(app_obj)
    return True


def review_app_by_id(session: SessionDep, request: Request, app_review: AppReview):
    """
    审核 APP
    :param session:
    :param request:
    :param Request:
    :param app_review:
    :return: bool
    """
    app_id = app_review.id
    review_status = app_review.reviewStatus
    review_msg = app_review.reviewMessage

    validate_request_exception(review_status not in (2, 1), '审核状态异常')

    sql = select(App).where(App.id == app_id)
    app_obj = session.exec(sql).first()
    validate_request_exception(not app_obj, '应用不存在')

    user_info = request.session.get('user_login_state')

    app_obj.review_status = review_status
    app_obj.review_message = review_msg
    app_obj.reviewer_id = user_info.get('id')
    app_obj.review_time = datetime.now()
    session.commit()
    session.refresh(app_obj)
    return True


def check_app_info(app_in: AppCreate):
    """
    检查应用
    :param app_in:
    :return:
    """
    app_name = app_in.appName
    app_desc = app_in.appDesc

    validate_request_exception(all([app_name, app_desc]), '应用名或描述不能为空')


def create_app(session: SessionDep, request: Request, app_in: AppCreate):
    """
    增加应用
    :param session:
    :param request:
    :param app_in:
    :return:
    """
    user_id = request.session.get('user_login_state').get('id')

    app_dict = app_in.to_dict()
    app_dict.update(user_id=user_id)
    app_obj = App(**app_dict)

    session.add(app_obj)
    session.commit()
    session.refresh(app_obj)

    return app_obj


def get_app_detail(app_id: int, session: SessionDep, request: Request):
    """
    通过id查询 APP 详情
    :param app_id:
    :param session:
    :param request:
    :return:
    """
    sql = select(App).where(App.id == app_id)
    app_obj = session.exec(sql).first()
    validate_request_exception(not app_obj, '应用记录不存在')

    app_dict = app_obj.to_dict()
    user_data = request.session.get('user_login_state')
    app_dict.update(user=user_data, userId=user_data.get('id'))
    return app_dict
