package net.irisshaders.iris.pipeline.foss_transform;

import net.irisshaders.iris.pipeline.transform.parameter.VanillaParameters;
import org.embeddedt.embeddium.impl.gl.shader.ShaderType;
import org.embeddedt.embeddium.impl.gl.util.IntegerVertexAttribCompat;
import org.taumc.glsl.Transformer;

public class EntityPatcherNew {
    public static void patchOverlayColor(Transformer translationUnit, VanillaParameters parameters) {
        if (translationUnit.hasVariable("entityColor")) {
            translationUnit.removeVariable("entityColor");
        }

        if (parameters.type == ShaderType.VERTEX) {
            translationUnit.injectVariable("uniform sampler2D iris_overlay;");
            translationUnit.injectVariable("out vec4 entityColor;");
            translationUnit.injectVariable("out vec4 iris_vertexColor;");
            translationUnit.injectVariable("in ivec2 iris_UV1;");

            translationUnit.prependMain("entityColor.rgb *= float(entityColor.a != 0.0);");
            translationUnit.prependMain("iris_vertexColor = iris_Color;");
            translationUnit.prependMain("entityColor = vec4(overlayColor.rgb, 1.0 - overlayColor.a);");
            translationUnit.prependMain("vec4 overlayColor = texelFetch(iris_overlay, iris_UV1, 0);");
        } else if (parameters.type == ShaderType.TESSELATION_CONTROL) {
            translationUnit.replaceExpression("entityColor", "entityColor[gl_InvocationID]");
            translationUnit.injectVariable("patch out vec4 entityColorTCS;");
            translationUnit.injectVariable("in vec4 entityColor[];");
            translationUnit.injectVariable("out vec4 iris_vertexColorTCS[];");
            translationUnit.injectVariable("in vec4 iris_vertexColor[];");
            translationUnit.prependMain(
                    "entityColorTCS = entityColor[gl_InvocationID];\n" +
                    "iris_vertexColorTCS[gl_InvocationID] = iris_vertexColor[gl_InvocationID];");
        } else if (parameters.type == ShaderType.TESSELATION_EVAL) {
            translationUnit.replaceExpression("entityColor", "entityColorTCS");
            translationUnit.injectVariable("out vec4 entityColorTES;");
            translationUnit.injectVariable("patch in vec4 entityColorTCS;");
            translationUnit.injectVariable("out vec4 iris_vertexColorTES;");
            translationUnit.injectFunction("in vec4 iris_vertexColorTCS[];");
            translationUnit.prependMain(
                    "entityColorTES = entityColorTCS;\n" +
                    "iris_vertexColorTES = iris_vertexColorTCS[0];");
        } else if (parameters.type == ShaderType.GEOMETRY) {
            translationUnit.replaceExpression("entityColor", "entityColor[0]");
            translationUnit.injectVariable("out vec4 entityColorGS;");
            translationUnit.injectVariable("in vec4 entityColor[];");
            translationUnit.injectVariable("out vec4 iris_vertexColorGS;");
            translationUnit.injectVariable("in vec4 iris_vertexColor[];");
            translationUnit.prependMain(
                    "entityColorGS = entityColor[0];\n" +
                    "iris_vertexColorGS = iris_vertexColor[0];");

            if (parameters.hasTesselation) {
                translationUnit.rename("iris_vertexColor", "iris_vertexColorTES");
                translationUnit.rename("entityColor", "entityColorTES");
            }
        } else if (parameters.type == ShaderType.FRAGMENT) {
            translationUnit.injectVariable("in vec4 entityColor;");
            translationUnit.injectVariable("in vec4 iris_vertexColor;");
            translationUnit.prependMain("float iris_vertexColorAlpha = iris_vertexColor.a;");

            if (parameters.hasGeometry) {
                translationUnit.rename("entityColor", "entityColorGS");
                translationUnit.rename("iris_vertexColor", "iris_vertexColorGS");
            } else if (parameters.hasTesselation) {
                translationUnit.rename("entityColor", "entityColorTES");
                translationUnit.rename("iris_vertexColor", "iris_vertexColorTES");
            }
        }
    }

    public static void patchEntityId(Transformer translationUnit, VanillaParameters parameters) {
        boolean integerAttributes = IntegerVertexAttribCompat.isIntegerAttributesSupported();
        String entityInfoType = integerAttributes ? "ivec3" : "vec3";
        String flatQualifier = integerAttributes ? "flat " : "";

        if (translationUnit.hasVariable("entityId")) {
            translationUnit.removeVariable("entityId");
        }
        if (translationUnit.hasVariable("blockEntityId")) {
            translationUnit.removeVariable("blockEntityId");
        }
        if (translationUnit.hasVariable("currentRenderedItemId")) {
            translationUnit.removeVariable("currentRenderedItemId");
        }

        if (parameters.type == ShaderType.GEOMETRY) {
            translationUnit.replaceExpression("entityId", entityInfoComponent("iris_entityInfo[0].x", integerAttributes));
            translationUnit.replaceExpression("blockEntityId", entityInfoComponent("iris_entityInfo[0].y", integerAttributes));
            translationUnit.replaceExpression("currentRenderedItemId", entityInfoComponent("iris_entityInfo[0].z", integerAttributes));
        } else {
            translationUnit.replaceExpression("entityId", entityInfoComponent("iris_entityInfo.x", integerAttributes));
            translationUnit.replaceExpression("blockEntityId", entityInfoComponent("iris_entityInfo.y", integerAttributes));
            translationUnit.replaceExpression("currentRenderedItemId", entityInfoComponent("iris_entityInfo.z", integerAttributes));
        }

        if (parameters.type == ShaderType.VERTEX) {
            translationUnit.injectVariable(flatQualifier + "out " + entityInfoType + " iris_entityInfo;");
            translationUnit.injectVariable("in " + entityInfoType + " iris_Entity;");
            translationUnit.prependMain("iris_entityInfo = iris_Entity;");
        } else if (parameters.type == ShaderType.TESSELATION_CONTROL) {
            translationUnit.injectVariable(flatQualifier + "out " + entityInfoType + " iris_entityInfoTCS[];");
            translationUnit.injectVariable(flatQualifier + "in " + entityInfoType + " iris_entityInfo[];");
            translationUnit.replaceExpression("iris_entityInfo", "iris_EntityInfo[gl_InvocationID]");
            translationUnit.prependMain("iris_entityInfoTCS[gl_InvocationID] = iris_entityInfo[gl_InvocationID];");
        } else if (parameters.type == ShaderType.TESSELATION_EVAL) {
            translationUnit.injectVariable(flatQualifier + "out " + entityInfoType + " iris_entityInfoTES;");
            translationUnit.injectVariable(flatQualifier + "in " + entityInfoType + " iris_entityInfoTCS[];");
            translationUnit.prependMain("iris_entityInfoTES = iris_entityInfoTCS[0];");
            translationUnit.replaceExpression("iris_entityInfo", "iris_EntityInfoTCS[0]");
        } else if (parameters.type == ShaderType.GEOMETRY) {
            translationUnit.injectVariable(flatQualifier + "out " + entityInfoType + " iris_entityInfoGS;");
            translationUnit.injectVariable(flatQualifier + "in " + entityInfoType + " iris_entityInfo" + (parameters.hasTesselation ? "TES" : "") + "[];");
            translationUnit.prependMain("iris_entityInfoGS = iris_entityInfo" + (parameters.hasTesselation ? "TES" : "") + "[0];");
        } else if (parameters.type == ShaderType.FRAGMENT) {
            translationUnit.injectVariable(flatQualifier + "in " + entityInfoType + " iris_entityInfo;");

            if (parameters.hasGeometry) {
                translationUnit.rename("iris_entityInfo", "iris_EntityInfoGS");
            } else if (parameters.hasTesselation) {
                translationUnit.rename("iris_entityInfo", "iris_entityInfoTES");
            }
        }
    }

    private static String entityInfoComponent(String expression, boolean integerAttributes) {
        return integerAttributes ? expression : "int(" + expression + ")";
    }
}
