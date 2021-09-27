""" The constants for decorators are saved here"""

PRE_CREATE = 'pre_create'
POST_CREATE = 'post_create'

PRE_SAVE = 'pre_save'
POST_SAVE = 'post_save'

PRE_DELETE = 'pre_delete'
POST_DELETE = 'post_delete'

FK_CHANGE = 'fk_change'
M2M_CHANGE = 'm2m_change'

# a set that contains event related to django's Related fields
RELATED_CHANGES = {FK_CHANGE, M2M_CHANGE}
