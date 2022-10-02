from rest_framework import permissions

class IsAuthenticatedOrCreating(permissions.BasePermission):
	"""
	The request is authenticated as a user, or is a postrequest.
	"""

	def has_permission(self, request, view):
		return request.user and request.user.is_authenticated or request.method == 'POST'