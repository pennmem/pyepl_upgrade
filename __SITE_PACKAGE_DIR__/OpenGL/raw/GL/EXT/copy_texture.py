'''OpenGL extension EXT.copy_texture

Automatically generated by the get_gl_extensions script, do not edit!
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_EXT_copy_texture'
_DEPRECATED = False

glCopyTexImage1DEXT = platform.createExtensionFunction( 
'glCopyTexImage1DEXT',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLint,constants.GLenum,constants.GLint,constants.GLint,constants.GLsizei,constants.GLint,),
doc='glCopyTexImage1DEXT(GLenum(target), GLint(level), GLenum(internalformat), GLint(x), GLint(y), GLsizei(width), GLint(border)) -> None',
argNames=('target','level','internalformat','x','y','width','border',),
deprecated=_DEPRECATED,
)

glCopyTexImage2DEXT = platform.createExtensionFunction( 
'glCopyTexImage2DEXT',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLint,constants.GLenum,constants.GLint,constants.GLint,constants.GLsizei,constants.GLsizei,constants.GLint,),
doc='glCopyTexImage2DEXT(GLenum(target), GLint(level), GLenum(internalformat), GLint(x), GLint(y), GLsizei(width), GLsizei(height), GLint(border)) -> None',
argNames=('target','level','internalformat','x','y','width','height','border',),
deprecated=_DEPRECATED,
)

glCopyTexSubImage1DEXT = platform.createExtensionFunction( 
'glCopyTexSubImage1DEXT',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLint,constants.GLint,constants.GLint,constants.GLint,constants.GLsizei,),
doc='glCopyTexSubImage1DEXT(GLenum(target), GLint(level), GLint(xoffset), GLint(x), GLint(y), GLsizei(width)) -> None',
argNames=('target','level','xoffset','x','y','width',),
deprecated=_DEPRECATED,
)

glCopyTexSubImage2DEXT = platform.createExtensionFunction( 
'glCopyTexSubImage2DEXT',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLint,constants.GLint,constants.GLint,constants.GLint,constants.GLint,constants.GLsizei,constants.GLsizei,),
doc='glCopyTexSubImage2DEXT(GLenum(target), GLint(level), GLint(xoffset), GLint(yoffset), GLint(x), GLint(y), GLsizei(width), GLsizei(height)) -> None',
argNames=('target','level','xoffset','yoffset','x','y','width','height',),
deprecated=_DEPRECATED,
)

glCopyTexSubImage3DEXT = platform.createExtensionFunction( 
'glCopyTexSubImage3DEXT',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLint,constants.GLint,constants.GLint,constants.GLint,constants.GLint,constants.GLint,constants.GLsizei,constants.GLsizei,),
doc='glCopyTexSubImage3DEXT(GLenum(target), GLint(level), GLint(xoffset), GLint(yoffset), GLint(zoffset), GLint(x), GLint(y), GLsizei(width), GLsizei(height)) -> None',
argNames=('target','level','xoffset','yoffset','zoffset','x','y','width','height',),
deprecated=_DEPRECATED,
)


def glInitCopyTextureEXT():
    '''Return boolean indicating whether this extension is available'''
    return extensions.hasGLExtension( EXTENSION_NAME )
