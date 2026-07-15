package org.embeddedt.embeddium.impl.gl.util;

import org.lwjgl.opengl.GL;
import org.lwjgl.opengl.GL30C;
import org.lwjgl.opengl.GLCapabilities;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;

/** Compatibility bridge for integer vertex attributes on OpenGL 2.1 macOS. */
public final class IntegerVertexAttribCompat {
    private static final MethodHandle EXT_ATTRIB_I3I = findExtMethod(
            "glVertexAttribI3iEXT",
            MethodType.methodType(void.class, int.class, int.class, int.class, int.class)
    );
    private static final MethodHandle EXT_ATTRIB_I_POINTER = findExtMethod(
            "glVertexAttribIPointerEXT",
            MethodType.methodType(void.class, int.class, int.class, int.class, int.class, long.class)
    );

    private IntegerVertexAttribCompat() {
    }

    public static void vertexAttribI3i(int index, int x, int y, int z) {
        GLCapabilities capabilities = GL.getCapabilities();
        if (capabilities.glVertexAttribI3i != 0L) {
            GL30C.glVertexAttribI3i(index, x, y, z);
            return;
        }
        if (capabilities.GL_EXT_gpu_shader4 && EXT_ATTRIB_I3I != null) {
            try {
                EXT_ATTRIB_I3I.invokeExact(index, x, y, z);
                return;
            } catch (Throwable throwable) {
                throw propagate(throwable);
            }
        }
        throw new UnsupportedOperationException("Integer vertex attributes are not supported by the current OpenGL context");
    }

    public static void vertexAttribIPointer(int index, int size, int type, int stride, long pointer) {
        GLCapabilities capabilities = GL.getCapabilities();
        if (capabilities.glVertexAttribIPointer != 0L) {
            GL30C.glVertexAttribIPointer(index, size, type, stride, pointer);
            return;
        }
        if (capabilities.GL_EXT_gpu_shader4 && EXT_ATTRIB_I_POINTER != null) {
            try {
                EXT_ATTRIB_I_POINTER.invokeExact(index, size, type, stride, pointer);
                return;
            } catch (Throwable throwable) {
                throw propagate(throwable);
            }
        }
        throw new UnsupportedOperationException("Integer vertex attributes are not supported by the current OpenGL context");
    }

    private static MethodHandle findExtMethod(String name, MethodType type) {
        try {
            Class<?> extensionClass = Class.forName("org.lwjgl.opengl.EXTGpuShader4");
            return MethodHandles.publicLookup().findStatic(extensionClass, name, type);
        } catch (ReflectiveOperationException ignored) {
            return null;
        }
    }

    private static RuntimeException propagate(Throwable throwable) {
        if (throwable instanceof RuntimeException) {
            return (RuntimeException) throwable;
        }
        if (throwable instanceof Error) {
            throw (Error) throwable;
        }
        return new RuntimeException(throwable);
    }
}
