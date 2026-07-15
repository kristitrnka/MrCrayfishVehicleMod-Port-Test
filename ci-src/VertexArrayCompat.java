package org.embeddedt.embeddium.impl.gl.util;

import org.lwjgl.opengl.GL;
import org.lwjgl.opengl.GL30C;
import org.lwjgl.opengl.GLCapabilities;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;

/**
 * Bridges core/ARB VAOs and Apple's legacy OpenGL 2.1 VAO extension.
 *
 * The common project is compiled against a reduced LWJGL API that does not
 * expose platform extension classes, so the Apple entry points are resolved
 * once at runtime from the full lwjgl-opengl jar supplied by Cleanroom.
 */
public final class VertexArrayCompat {
    private static final MethodHandle APPLE_BIND = findAppleMethod("glBindVertexArrayAPPLE", MethodType.methodType(void.class, int.class));
    private static final MethodHandle APPLE_GENERATE = findAppleMethod("glGenVertexArraysAPPLE", MethodType.methodType(int.class));
    private static final MethodHandle APPLE_DELETE = findAppleMethod("glDeleteVertexArraysAPPLE", MethodType.methodType(void.class, int.class));

    private VertexArrayCompat() {
    }

    public static boolean isSupported() {
        GLCapabilities capabilities = GL.getCapabilities();
        return capabilities.glBindVertexArray != 0L ||
                (capabilities.GL_APPLE_vertex_array_object && APPLE_BIND != null && APPLE_GENERATE != null && APPLE_DELETE != null);
    }

    public static int generate() {
        GLCapabilities capabilities = GL.getCapabilities();
        if (capabilities.glGenVertexArrays != 0L) {
            return GL30C.glGenVertexArrays();
        }
        if (capabilities.GL_APPLE_vertex_array_object && APPLE_GENERATE != null) {
            try {
                return (int) APPLE_GENERATE.invokeExact();
            } catch (Throwable throwable) {
                throw propagate(throwable);
            }
        }
        throw new UnsupportedOperationException("Vertex array objects are not supported by the current OpenGL context");
    }

    public static void bind(int array) {
        GLCapabilities capabilities = GL.getCapabilities();
        if (capabilities.glBindVertexArray != 0L) {
            GL30C.glBindVertexArray(array);
            return;
        }
        if (capabilities.GL_APPLE_vertex_array_object && APPLE_BIND != null) {
            try {
                APPLE_BIND.invokeExact(array);
                return;
            } catch (Throwable throwable) {
                throw propagate(throwable);
            }
        }
        if (array != 0) {
            throw new UnsupportedOperationException("Vertex array objects are not supported by the current OpenGL context");
        }
    }

    public static void delete(int array) {
        if (array == 0) {
            return;
        }

        GLCapabilities capabilities = GL.getCapabilities();
        if (capabilities.glDeleteVertexArrays != 0L) {
            GL30C.glDeleteVertexArrays(array);
            return;
        }
        if (capabilities.GL_APPLE_vertex_array_object && APPLE_DELETE != null) {
            try {
                APPLE_DELETE.invokeExact(array);
                return;
            } catch (Throwable throwable) {
                throw propagate(throwable);
            }
        }
        throw new UnsupportedOperationException("Vertex array objects are not supported by the current OpenGL context");
    }

    private static MethodHandle findAppleMethod(String name, MethodType type) {
        try {
            Class<?> extensionClass = Class.forName("org.lwjgl.opengl.APPLEVertexArrayObject");
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
