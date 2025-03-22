#  IRIS Source Code
#  Copyright (C) 2023 - DFIR-IRIS
#  contact@dfir-iris.org
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
from typing import Tuple

from flask_login import current_user

from app.models import Comments
from app import db


def get_case_comment(comment_id, caseid):
    if caseid is None:
        return Comments.query.filter(
            Comments.comment_id == comment_id
        ).first()
    else:
        return Comments.query.filter(
            Comments.comment_id == comment_id,
            Comments.comment_case_id == caseid
        ).first()

def get_case_comments(caseid):
    return Comments.query.filter(
        Comments.comment_alert_id.is_(None),
        Comments.comment_case_id == caseid
    ).order_by(
        Comments.comment_date.asc()
    ).all()

def delete_case_comment(comment_id: int, caseid: int) -> Tuple[bool, str]:
    """
    Delete a comment of a case

    args:
        comment_id (int): The ID of the comment
    """
    comment = Comments.query.filter(
        Comments.comment_id == comment_id,
        Comments.comment_user_id == current_user.id,
        Comments.comment_case_id == caseid
    ).first()
    if not comment:
        return False, "You are not allowed to delete this comment"

    db.session.delete(comment)
    db.session.commit()

    return True, "Comment deleted successfully"
