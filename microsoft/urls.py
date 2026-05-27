from django.urls import path

from .views import presence, chat, onedrive, tasks, contacts

app_name = "microsoft"

urlpatterns = [
    # ── Presence ──────────────────────────────────────────────────────
    path("presence/", presence.presence_view, name="presence"),
    path("api/presence/", presence.presence_api, name="presence_api"),
    path("api/presence/team/", presence.team_presence_api, name="team_presence_api"),

    # ── Chat ──────────────────────────────────────────────────────────
    path("chat/", chat.chat_view, name="chat"),
    path("api/chat/<str:chat_id>/messages/", chat.chat_messages_api, name="chat_messages"),
    path("api/chat/<str:chat_id>/send/", chat.send_chat_message_api, name="send_chat_message"),
    path("api/teams-channels/", chat.teams_channels_api, name="teams_channels_api"),
    path("api/teams/<str:team_id>/channels/<str:channel_id>/messages/", chat.channel_messages_api, name="channel_messages"),
    path("api/teams/<str:team_id>/channels/<str:channel_id>/send/", chat.send_channel_message_api, name="send_channel_message"),

    # ── OneDrive ──────────────────────────────────────────────────────
    path("onedrive/", onedrive.browser_view, name="onedrive"),
    path("api/files/", onedrive.list_files_api, name="list_files"),
    path("api/files/search/", onedrive.search_files_api, name="search_files"),
    path("api/files/<str:item_id>/download/", onedrive.download_file_api, name="download_file"),
    path("api/files/upload/", onedrive.upload_file_api, name="upload_file"),
    path("api/files/folder/", onedrive.create_folder_api, name="create_folder"),
    path("api/files/<str:item_id>/delete/", onedrive.delete_item_api, name="delete_item"),
    path("api/files/<str:item_id>/share/", onedrive.share_link_api, name="share_link"),

    # ── To Do ─────────────────────────────────────────────────────────
    path("todo/", tasks.todo_view, name="todo"),
    path("api/todo/<str:list_id>/tasks/", tasks.todo_tasks_api, name="todo_tasks"),
    path("api/todo/<str:list_id>/tasks/create/", tasks.create_task_api, name="create_task"),
    path("api/todo/<str:list_id>/tasks/<str:task_id>/update/", tasks.update_task_api, name="update_task"),
    path("api/todo/<str:list_id>/tasks/<str:task_id>/delete/", tasks.delete_task_api, name="delete_task"),
    path("api/todo/lists/create/", tasks.create_list_api, name="create_list"),

    # ── Planner ───────────────────────────────────────────────────────
    path("planner/", tasks.planner_view, name="planner"),
    path("api/planner/tasks/", tasks.planner_tasks_api, name="planner_tasks"),

    # ── Contacts ──────────────────────────────────────────────────────
    path("contacts/", contacts.people_view, name="contacts"),
    path("api/people/", contacts.people_api, name="people_api"),
    path("api/directory/", contacts.directory_api, name="directory_api"),
]
