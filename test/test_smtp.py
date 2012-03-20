'''
Created on Jun 13, 2011

@author: thatcherclay
'''
from twisted.trial import unittest
from twisted.cred.credentials import UsernamePassword
from twisted.cred.error import UnauthorizedLogin

from core.smtp import DjangoAuthChecker
from test.seed import createUser

class DjangoAuthCheckerTestSuite(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def _assertUserEqual(self, user, expectedUserName):
        self.assertEqual(expectedUserName, user.username)
    
    
    def test_authenticatesValidUser(self):
        createUser('test1@mailreceipts.com','pass1')
        
        checker = DjangoAuthChecker()
        user = checker.requestAvatarId(UsernamePassword('test1@mailreceipts.com',"pass1"))
        user.addCallback(self._assertUserEqual,'test1@mailreceipts.com')
        
    
    def test_failsOnInvalidUser(self):
        createUser('test1@mailreceipts.com','pass1')
        
        checker = DjangoAuthChecker()
        user= checker.requestAvatarId(UsernamePassword("test_wrong_username","pass1"))
        self.assertFailure(user, UnauthorizedLogin) 
    
    def test_failsOnInvalidPassword(self):
        createUser('test1@mailreceipts.com','pass1')
        
        checker = DjangoAuthChecker()
        user= checker.requestAvatarId(UsernamePassword('test1@mailreceipts.com',"wrong_password"))
        self.assertFailure(user, UnauthorizedLogin) 

if __name__ == '__main__':
    unittest.main()