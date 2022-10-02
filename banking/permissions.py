from rest_framework import permissions

class IsAuthenticatedOrCreating(permissions.BasePermission):
	"""
	The request is authenticated as a user, or is a postrequest.
	"""

	def has_permission(self, request, view):
		if request.method == 'POST' and not request.user.is_authenticated:
			return True
		return request.user and request.user.is_authenticated