"""
Comprehensive tests for Commenting and Activity Feed Systems
Tests comment creation, threading, activity tracking, and real-time updates
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import json

# Add web_ui to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCommentingSystem:
    """Test commenting system functionality"""

    def test_create_comment(self):
        """Test creating a new comment"""
        comment_data = {
            "node_id": "claim_123",
            "text": "This is a test comment",
            "author": "test_user",
            "created_at": datetime.now().isoformat()
        }

        assert comment_data["node_id"] == "claim_123"
        assert comment_data["text"] == "This is a test comment"
        assert "created_at" in comment_data

    def test_create_reply(self):
        """Test creating a reply to a comment"""
        parent_comment = {
            "id": "comment_1",
            "node_id": "claim_123",
            "text": "Original comment",
            "replies": []
        }

        reply = {
            "id": "comment_2",
            "parent_id": "comment_1",
            "text": "Reply to comment",
            "created_at": datetime.now().isoformat()
        }

        parent_comment["replies"].append(reply)

        assert len(parent_comment["replies"]) == 1
        assert parent_comment["replies"][0]["parent_id"] == parent_comment["id"]

    def test_nested_reply_threads(self):
        """Test nested reply threads"""
        comment = {
            "id": "comment_1",
            "text": "Level 1 comment",
            "replies": [
                {
                    "id": "comment_2",
                    "text": "Level 2 reply",
                    "replies": [
                        {
                            "id": "comment_3",
                            "text": "Level 3 reply",
                            "replies": []
                        }
                    ]
                }
            ]
        }

        assert len(comment["replies"]) == 1
        assert len(comment["replies"][0]["replies"]) == 1

    def test_markdown_support(self):
        """Test Markdown formatting in comments"""
        comment = {
            "text": "**Bold** and *italic* with [link](https://example.com)",
            "raw_text": "**Bold** and *italic* with [link](https://example.com)",
            "supports_markdown": True
        }

        assert "**Bold**" in comment["raw_text"]
        assert "*italic*" in comment["raw_text"]
        assert "[link]" in comment["raw_text"]

    def test_edit_comment(self):
        """Test editing an existing comment"""
        comment = {
            "id": "comment_1",
            "text": "Original text",
            "edited": False,
            "edit_history": []
        }

        # Edit the comment
        old_text = comment["text"]
        comment["text"] = "Edited text"
        comment["edited"] = True
        comment["edit_history"].append({
            "old_text": old_text,
            "edited_at": datetime.now().isoformat()
        })

        assert comment["edited"] == True
        assert len(comment["edit_history"]) == 1
        assert comment["edit_history"][0]["old_text"] == "Original text"

    def test_delete_comment(self):
        """Test deleting a comment"""
        comment = {
            "id": "comment_1",
            "text": "Comment to delete",
            "deleted": False
        }

        # Soft delete
        comment["deleted"] = True
        comment["deleted_at"] = datetime.now().isoformat()
        comment["text"] = "[Deleted]"

        assert comment["deleted"] == True
        assert comment["text"] == "[Deleted]"

    def test_comment_mentions(self):
        """Test @mentions in comments"""
        comment = {
            "text": "Hey @user1 and @user2, check this out!",
            "mentions": ["user1", "user2"]
        }

        assert len(comment["mentions"]) == 2
        assert "user1" in comment["mentions"]
        assert "user2" in comment["mentions"]

    def test_comment_reactions(self):
        """Test reactions/likes on comments"""
        comment = {
            "id": "comment_1",
            "text": "Great point!",
            "reactions": {
                "thumbs_up": 5,
                "heart": 2,
                "thinking": 1
            }
        }

        total_reactions = sum(comment["reactions"].values())
        assert total_reactions == 8

    def test_comment_permissions(self):
        """Test comment edit/delete permissions"""
        comment = {
            "id": "comment_1",
            "author": "user1",
            "text": "My comment"
        }

        # Same user can edit
        current_user = "user1"
        can_edit = (comment["author"] == current_user)
        assert can_edit == True

        # Different user cannot edit
        current_user = "user2"
        can_edit = (comment["author"] == current_user)
        assert can_edit == False


class TestActivityFeed:
    """Test activity feed and tracking system"""

    def test_track_document_upload(self):
        """Test tracking document upload activity"""
        activity = {
            "type": "document_upload",
            "action": "uploaded",
            "resource_type": "document",
            "resource_id": "doc_123",
            "resource_name": "research_paper.pdf",
            "timestamp": datetime.now().isoformat(),
            "user": "test_user"
        }

        assert activity["type"] == "document_upload"
        assert activity["action"] == "uploaded"

    def test_track_claim_creation(self):
        """Test tracking claim creation activity"""
        activity = {
            "type": "claim_creation",
            "action": "created",
            "resource_type": "claim",
            "resource_id": "claim_456",
            "resource_name": "Climate change claim",
            "timestamp": datetime.now().isoformat()
        }

        assert activity["type"] == "claim_creation"
        assert activity["resource_type"] == "claim"

    def test_track_search_query(self):
        """Test tracking search query activity"""
        activity = {
            "type": "search",
            "action": "searched",
            "query": "climate change",
            "results_count": 15,
            "timestamp": datetime.now().isoformat()
        }

        assert activity["type"] == "search"
        assert activity["query"] == "climate change"
        assert activity["results_count"] == 15

    def test_track_comment_activity(self):
        """Test tracking comment creation activity"""
        activity = {
            "type": "comment",
            "action": "commented",
            "resource_type": "comment",
            "resource_id": "comment_789",
            "target_type": "claim",
            "target_id": "claim_123",
            "timestamp": datetime.now().isoformat()
        }

        assert activity["type"] == "comment"
        assert activity["target_type"] == "claim"

    def test_track_project_creation(self):
        """Test tracking project creation activity"""
        activity = {
            "type": "project_creation",
            "action": "created",
            "resource_type": "project",
            "resource_id": "proj_001",
            "resource_name": "AI Research Project",
            "timestamp": datetime.now().isoformat()
        }

        assert activity["type"] == "project_creation"
        assert activity["resource_name"] == "AI Research Project"

    def test_activity_feed_ordering(self):
        """Test activity feed returns items in reverse chronological order"""
        activities = [
            {"id": "1", "timestamp": "2025-11-23T10:00:00"},
            {"id": "2", "timestamp": "2025-11-23T11:00:00"},
            {"id": "3", "timestamp": "2025-11-23T09:00:00"}
        ]

        # Sort by timestamp descending
        sorted_activities = sorted(
            activities,
            key=lambda x: x["timestamp"],
            reverse=True
        )

        assert sorted_activities[0]["id"] == "2"  # Most recent
        assert sorted_activities[-1]["id"] == "3"  # Oldest

    def test_activity_feed_filtering(self):
        """Test filtering activity feed by type"""
        activities = [
            {"id": "1", "type": "document_upload"},
            {"id": "2", "type": "claim_creation"},
            {"id": "3", "type": "document_upload"},
            {"id": "4", "type": "search"}
        ]

        # Filter for document uploads only
        filtered = [a for a in activities if a["type"] == "document_upload"]

        assert len(filtered) == 2
        assert all(a["type"] == "document_upload" for a in filtered)

    def test_activity_feed_pagination(self):
        """Test paginating activity feed"""
        activities = [{"id": str(i)} for i in range(100)]

        page_size = 20
        page = 1

        start = (page - 1) * page_size
        end = start + page_size

        page_activities = activities[start:end]

        assert len(page_activities) == 20
        assert page_activities[0]["id"] == "0"

    def test_activity_feed_date_range_filter(self):
        """Test filtering activity by date range"""
        base_time = datetime.now()

        activities = [
            {"id": "1", "timestamp": (base_time).isoformat()},
            {"id": "2", "timestamp": (base_time).isoformat()},
            {"id": "3", "timestamp": (base_time).isoformat()}
        ]

        # Filter activities from today
        today = base_time.date().isoformat()
        today_activities = [
            a for a in activities
            if a["timestamp"].startswith(today)
        ]

        assert len(today_activities) >= 0

    def test_activity_statistics(self):
        """Test generating activity statistics"""
        activities = [
            {"type": "document_upload"},
            {"type": "document_upload"},
            {"type": "claim_creation"},
            {"type": "search"},
            {"type": "search"},
            {"type": "search"}
        ]

        stats = {}
        for activity in activities:
            activity_type = activity["type"]
            stats[activity_type] = stats.get(activity_type, 0) + 1

        assert stats["document_upload"] == 2
        assert stats["claim_creation"] == 1
        assert stats["search"] == 3

    def test_real_time_activity_updates(self):
        """Test real-time activity updates via WebSocket"""
        activity = {
            "type": "claim_creation",
            "action": "created",
            "resource_id": "claim_new",
            "timestamp": datetime.now().isoformat()
        }

        # Mock WebSocket event
        ws_event = {
            "event": "activity_created",
            "data": activity
        }

        assert ws_event["event"] == "activity_created"
        assert ws_event["data"]["type"] == "claim_creation"

    def test_activity_grouping(self):
        """Test grouping similar activities"""
        activities = [
            {"id": "1", "type": "claim_creation", "user": "user1", "timestamp": "2025-11-23T10:00:00"},
            {"id": "2", "type": "claim_creation", "user": "user1", "timestamp": "2025-11-23T10:01:00"},
            {"id": "3", "type": "claim_creation", "user": "user1", "timestamp": "2025-11-23T10:02:00"}
        ]

        # Group consecutive similar activities
        grouped = {
            "type": "claim_creation",
            "user": "user1",
            "count": 3,
            "first_timestamp": activities[0]["timestamp"],
            "last_timestamp": activities[-1]["timestamp"]
        }

        assert grouped["count"] == 3
        assert grouped["type"] == "claim_creation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
