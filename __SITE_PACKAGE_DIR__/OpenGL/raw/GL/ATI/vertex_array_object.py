'''OpenGL extension ATI.vertex_array_object

Automatically generated by the get_gl_extensions script, do not edit!
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_ATI_vertex_array_object'
_DEPRECATED = False
GL_STATIC_ATI = constant.Constant( 'GL_STATIC_ATI', 0x8760 )
GL_DYNAMIC_ATI = constant.Constant( 'GL_DYNAMIC_ATI', 0x8761 )
GL_PRESERVE_ATI = constant.Constant( 'GL_PRESERVE_ATI', 0x8762 )
GL_DISCARD_ATI = constant.Constant( 'GL_DISCARD_ATI', 0x8763 )
GL_OBJECT_BUFFER_SIZE_ATI = constant.Constant( 'GL_OBJECT_BUFFER_SIZE_ATI', 0x8764 )
GL_OBJECT_BUFFER_USAGE_ATI = constant.Constant( 'GL_OBJECT_BUFFER_USAGE_ATI', 0x8765 )
GL_ARRAY_OBJECT_BUFFER_ATI = constant.Constant( 'GL_ARRAY_OBJECT_BUFFER_ATI', 0x8766 )
GL_ARRAY_OBJECT_OFFSET_ATI = constant.Constant( 'GL_ARRAY_OBJECT_OFFSET_ATI', 0x8767 )
glNewObjectBufferATI = platform.createExtensionFunction( 
'glNewObjectBufferATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=constants.GLuint, 
argTypes=(constants.GLsizei,ctypes.c_void_p,constants.GLenum,),
doc='glNewObjectBufferATI(GLsizei(size), c_void_p(pointer), GLenum(usage)) -> constants.GLuint',
argNames=('size','pointer','usage',),
deprecated=_DEPRECATED,
)

glIsObjectBufferATI = platform.createExtensionFunction( 
'glIsObjectBufferATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=constants.GLboolean, 
argTypes=(constants.GLuint,),
doc='glIsObjectBufferATI(GLuint(buffer)) -> constants.GLboolean',
argNames=('buffer',),
deprecated=_DEPRECATED,
)

glUpdateObjectBufferATI = platform.createExtensionFunction( 
'glUpdateObjectBufferATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLuint,constants.GLuint,constants.GLsizei,ctypes.c_void_p,constants.GLenum,),
doc='glUpdateObjectBufferATI(GLuint(buffer), GLuint(offset), GLsizei(size), c_void_p(pointer), GLenum(preserve)) -> None',
argNames=('buffer','offset','size','pointer','preserve',),
deprecated=_DEPRECATED,
)

glGetObjectBufferfvATI = platform.createExtensionFunction( 
'glGetObjectBufferfvATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLuint,constants.GLenum,arrays.GLfloatArray,),
doc='glGetObjectBufferfvATI(GLuint(buffer), GLenum(pname), GLfloatArray(params)) -> None',
argNames=('buffer','pname','params',),
deprecated=_DEPRECATED,
)

glGetObjectBufferivATI = platform.createExtensionFunction( 
'glGetObjectBufferivATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLuint,constants.GLenum,arrays.GLintArray,),
doc='glGetObjectBufferivATI(GLuint(buffer), GLenum(pname), GLintArray(params)) -> None',
argNames=('buffer','pname','params',),
deprecated=_DEPRECATED,
)

glFreeObjectBufferATI = platform.createExtensionFunction( 
'glFreeObjectBufferATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLuint,),
doc='glFreeObjectBufferATI(GLuint(buffer)) -> None',
argNames=('buffer',),
deprecated=_DEPRECATED,
)

glArrayObjectATI = platform.createExtensionFunction( 
'glArrayObjectATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLint,constants.GLenum,constants.GLsizei,constants.GLuint,constants.GLuint,),
doc='glArrayObjectATI(GLenum(array), GLint(size), GLenum(type), GLsizei(stride), GLuint(buffer), GLuint(offset)) -> None',
argNames=('array','size','type','stride','buffer','offset',),
deprecated=_DEPRECATED,
)

glGetArrayObjectfvATI = platform.createExtensionFunction( 
'glGetArrayObjectfvATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLenum,arrays.GLfloatArray,),
doc='glGetArrayObjectfvATI(GLenum(array), GLenum(pname), GLfloatArray(params)) -> None',
argNames=('array','pname','params',),
deprecated=_DEPRECATED,
)

glGetArrayObjectivATI = platform.createExtensionFunction( 
'glGetArrayObjectivATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLenum,arrays.GLintArray,),
doc='glGetArrayObjectivATI(GLenum(array), GLenum(pname), GLintArray(params)) -> None',
argNames=('array','pname','params',),
deprecated=_DEPRECATED,
)

glVariantArrayObjectATI = platform.createExtensionFunction( 
'glVariantArrayObjectATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLuint,constants.GLenum,constants.GLsizei,constants.GLuint,constants.GLuint,),
doc='glVariantArrayObjectATI(GLuint(id), GLenum(type), GLsizei(stride), GLuint(buffer), GLuint(offset)) -> None',
argNames=('id','type','stride','buffer','offset',),
deprecated=_DEPRECATED,
)

glGetVariantArrayObjectfvATI = platform.createExtensionFunction( 
'glGetVariantArrayObjectfvATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLuint,constants.GLenum,arrays.GLfloatArray,),
doc='glGetVariantArrayObjectfvATI(GLuint(id), GLenum(pname), GLfloatArray(params)) -> None',
argNames=('id','pname','params',),
deprecated=_DEPRECATED,
)

glGetVariantArrayObjectivATI = platform.createExtensionFunction( 
'glGetVariantArrayObjectivATI',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLuint,constants.GLenum,arrays.GLintArray,),
doc='glGetVariantArrayObjectivATI(GLuint(id), GLenum(pname), GLintArray(params)) -> None',
argNames=('id','pname','params',),
deprecated=_DEPRECATED,
)


def glInitVertexArrayObjectATI():
    '''Return boolean indicating whether this extension is available'''
    return extensions.hasGLExtension( EXTENSION_NAME )