
from django.contrib.auth.models import User, check_password
from twisted.cred import checkers, credentials
from twisted.internet import threads, defer, error as credError
from twisted.python import failure
from zope.interface.declarations import implements
import logging

logger = logging.getLogger("access")

class DjangoAuthChecker:
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,
                            credentials.IUsernameHashedPassword)

    def _checkPassword(self, user, password):
      if user.check_password(password):
        logger.info('Authorization passed for %s'%str(user))
        return user
      else:
        logger.warning('Unauthorized login: %s'% user)
        return failure.Failure(credError.UnauthorizedLogin())

    def _getUser(self, credentials):
      return User.objects.get(username=credentials.username)

    def requestAvatarId(self, credentials):
        try:
            deferred = threads.deferToThread(self._getUser, credentials)
            deferred.addCallback(self._checkPassword, credentials.password)
            return deferred
        except:
            return defer.fail(credError.UnauthorizedLogin())