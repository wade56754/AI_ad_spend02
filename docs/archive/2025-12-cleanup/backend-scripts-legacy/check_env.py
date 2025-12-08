import os
orig = os.getenv('ALLOWED_ORIGINS')
print('Value:', repr(orig))
print('Type:', type(orig))
if orig:
    print('Split:', orig.split(','))