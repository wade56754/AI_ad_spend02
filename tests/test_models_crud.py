#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模型 CRUD 测试

验证常用关系能正常使用，包括：
- 创建、查询、更新、删除操作
- relationship 关系的正确性
"""

import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime

from backend.models import (
    User, Project, AdAccount, Channel,
    TopupRequest, LedgerEntry, DailyReport,
    ReconciliationBatch, ReconciliationDetail
)
from backend.models.enums import (
    ProjectStatus, AdAccountStatus, TopupRequestStatus,
    DailyReportStatus, ReconciliationBatchStatus
)


@pytest.mark.integration
class TestModelCRUD:
    """模型 CRUD 测试"""
    
    def test_user_crud(self, db_session):
        """测试 User 模型的 CRUD"""
        # Create
        user = User(
            id=uuid4(),
            username=f"test_user_{uuid4().hex[:8]}",
            email=f"test_{uuid4().hex[:8]}@test.com",
            hashed_password="hashed_password_123",
            role="admin",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Read
        found_user = db_session.query(User).filter(User.id == user.id).first()
        assert found_user is not None
        assert found_user.username == user.username
        
        # Update
        found_user.is_active = False
        db_session.commit()
        
        updated_user = db_session.query(User).filter(User.id == user.id).first()
        assert updated_user.is_active == False
        
        # Delete
        db_session.delete(updated_user)
        db_session.commit()
        
        deleted_user = db_session.query(User).filter(User.id == user.id).first()
        assert deleted_user is None
    
    def test_project_crud(self, db_session, test_user):
        """测试 Project 模型的 CRUD"""
        # Create
        project = Project(
            project_name=f"测试项目_{uuid4().hex[:8]}",
            project_code=f"PRJ_{uuid4().hex[:8]}",
            client_name="测试客户",
            status=ProjectStatus.DRAFT.value,
            created_by=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # Read
        found_project = db_session.query(Project).filter(Project.id == project.id).first()
        assert found_project is not None
        assert found_project.project_name == project.project_name
        
        # Update
        found_project.status = ProjectStatus.ACTIVE.value
        db_session.commit()
        
        updated_project = db_session.query(Project).filter(Project.id == project.id).first()
        assert updated_project.status == ProjectStatus.ACTIVE.value
        
        # Delete
        db_session.delete(updated_project)
        db_session.commit()
    
    def test_project_user_relationship(self, db_session, test_user):
        """测试 Project 与 User 的 relationship"""
        project = Project(
            project_name=f"测试项目_{uuid4().hex[:8]}",
            project_code=f"PRJ_{uuid4().hex[:8]}",
            client_name="测试客户",
            status=ProjectStatus.DRAFT.value,
            created_by=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # 测试 relationship
        assert project.creator is not None
        assert project.creator.id == test_user.id
    
    def test_project_ad_account_relationship(self, db_session, test_user):
        """测试 Project 与 AdAccount 的 relationship"""
        # 创建项目
        project = Project(
            project_name=f"测试项目_{uuid4().hex[:8]}",
            project_code=f"PRJ_{uuid4().hex[:8]}",
            client_name="测试客户",
            status=ProjectStatus.ACTIVE.value,
            created_by=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # 创建渠道
        channel = Channel(
            id=uuid4(),
            name="测试渠道",
            channel_code=f"CH_{uuid4().hex[:8]}",
            status="active",
            created_by=test_user.id
        )
        db_session.add(channel)
        db_session.commit()
        
        # 创建广告账户
        ad_account = AdAccount(
            account_code=f"ACC_{uuid4().hex[:8]}",
            account_name="测试账户",
            project_id=project.id,
            channel_id=channel.id,
            status=AdAccountStatus.NEW.value,
            owner_id=test_user.id
        )
        db_session.add(ad_account)
        db_session.commit()
        
        # 测试 relationship
        assert ad_account.project is not None
        assert ad_account.project.id == project.id
        assert ad_account in project.ad_accounts
    
    def test_ad_account_channel_relationship(self, db_session, test_user):
        """测试 AdAccount 与 Channel 的 relationship"""
        channel = Channel(
            id=uuid4(),
            name="测试渠道",
            channel_code=f"CH_{uuid4().hex[:8]}",
            status="active",
            created_by=test_user.id
        )
        db_session.add(channel)
        db_session.commit()
        
        project = Project(
            project_name=f"测试项目_{uuid4().hex[:8]}",
            project_code=f"PRJ_{uuid4().hex[:8]}",
            client_name="测试客户",
            status=ProjectStatus.ACTIVE.value,
            created_by=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        ad_account = AdAccount(
            account_code=f"ACC_{uuid4().hex[:8]}",
            account_name="测试账户",
            project_id=project.id,
            channel_id=channel.id,
            status=AdAccountStatus.NEW.value,
            owner_id=test_user.id
        )
        db_session.add(ad_account)
        db_session.commit()
        
        # 测试 relationship
        assert ad_account.channel is not None
        assert ad_account.channel.id == channel.id
        assert ad_account in channel.ad_accounts
    
    def test_topup_request_relationship(self, db_session, test_user):
        """测试 TopupRequest 的 relationship"""
        project = Project(
            project_name=f"测试项目_{uuid4().hex[:8]}",
            project_code=f"PRJ_{uuid4().hex[:8]}",
            client_name="测试客户",
            status=ProjectStatus.ACTIVE.value,
            created_by=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        channel = Channel(
            id=uuid4(),
            name="测试渠道",
            channel_code=f"CH_{uuid4().hex[:8]}",
            status="active",
            created_by=test_user.id
        )
        db_session.add(channel)
        db_session.commit()
        
        ad_account = AdAccount(
            account_code=f"ACC_{uuid4().hex[:8]}",
            account_name="测试账户",
            project_id=project.id,
            channel_id=channel.id,
            status=AdAccountStatus.ACTIVE.value,
            owner_id=test_user.id
        )
        db_session.add(ad_account)
        db_session.commit()
        
        topup_request = TopupRequest(
            ad_account_id=ad_account.id,
            amount=Decimal("1000.00"),
            status=TopupRequestStatus.DRAFT.value,
            requested_by=test_user.id
        )
        db_session.add(topup_request)
        db_session.commit()
        
        # 测试 relationship
        assert topup_request.ad_account is not None
        assert topup_request.ad_account.id == ad_account.id
        assert topup_request.requester is not None
        assert topup_request.requester.id == test_user.id
    
    def test_daily_report_relationship(self, db_session, test_user):
        """测试 DailyReport 的 relationship"""
        project = Project(
            project_name=f"测试项目_{uuid4().hex[:8]}",
            project_code=f"PRJ_{uuid4().hex[:8]}",
            client_name="测试客户",
            status=ProjectStatus.ACTIVE.value,
            created_by=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        channel = Channel(
            id=uuid4(),
            name="测试渠道",
            channel_code=f"CH_{uuid4().hex[:8]}",
            status="active",
            created_by=test_user.id
        )
        db_session.add(channel)
        db_session.commit()
        
        ad_account = AdAccount(
            account_code=f"ACC_{uuid4().hex[:8]}",
            account_name="测试账户",
            project_id=project.id,
            channel_id=channel.id,
            status=AdAccountStatus.ACTIVE.value,
            owner_id=test_user.id
        )
        db_session.add(ad_account)
        db_session.commit()
        
        daily_report = DailyReport(
            ad_account_id=ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.DRAFT.value,
            submitted_by=test_user.id
        )
        db_session.add(daily_report)
        db_session.commit()
        
        # 测试 relationship
        assert daily_report.ad_account is not None
        assert daily_report.ad_account.id == ad_account.id
        assert daily_report.submitter is not None
        assert daily_report.submitter.id == test_user.id



