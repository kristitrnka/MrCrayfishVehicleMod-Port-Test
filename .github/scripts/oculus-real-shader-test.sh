#!/usr/bin/env bash
set -Eeuo pipefail

RESULT_BRANCH="automation/oculus-real-shader-validation"
RESULT_DIR="$RUNNER_TEMP/oculus-validation-results"
OCULUS_ROOT="$RUNNER_TEMP/Oculus"
PROJECT_DIR="$OCULUS_ROOT/oculus-1.12.2"
MC_DIR="$RUNNER_TEMP/minecraft-shader-test"
SERVER_DIR="$RUNNER_TEMP/vanilla-server"
mkdir -p "$RESULT_DIR"
printf 'running\n' > "$RESULT_DIR/status.txt"

publish_results() {
  code=$?
  set +e
  printf '%s\n' "$code" > "$RESULT_DIR/exit-code.txt"
  if [ "$code" -eq 0 ]; then
    printf 'success\n' > "$RESULT_DIR/status.txt"
  else
    printf 'failure\n' > "$RESULT_DIR/status.txt"
  fi

  test -f "$PROJECT_DIR/build/libs/oculus-0.1.0.jar" && cp "$PROJECT_DIR/build/libs/oculus-0.1.0.jar" "$RESULT_DIR/oculus-0.1.0-real-shader-tested.jar"
  test -f "$PROJECT_DIR/build.log" && cp "$PROJECT_DIR/build.log" "$RESULT_DIR/build.log"
  test -f "$MC_DIR/shader-runtime.log" && cp "$MC_DIR/shader-runtime.log" "$RESULT_DIR/shader-runtime.log"
  test -f "$MC_DIR/logs/latest.log" && cp "$MC_DIR/logs/latest.log" "$RESULT_DIR/latest.log"
  test -f "$SERVER_DIR/server.log" && cp "$SERVER_DIR/server.log" "$RESULT_DIR/server.log"
  test -f /tmp/xorg.log && cp /tmp/xorg.log "$RESULT_DIR/xorg.log"
  screenshot=$(find "$MC_DIR/screenshots" -maxdepth 1 -type f -name '*.png' 2>/dev/null | sort | tail -n 1)
  test -n "${screenshot:-}" && cp "$screenshot" "$RESULT_DIR/shader-world.png"
  sha256sum "$RESULT_DIR"/*.jar > "$RESULT_DIR/sha256.txt" 2>/dev/null || true

  git config user.name "github-actions[bot]"
  git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
  git fetch origin "$RESULT_BRANCH"
  rm -rf "$RUNNER_TEMP/results-worktree"
  git worktree add -B "$RESULT_BRANCH" "$RUNNER_TEMP/results-worktree" "origin/$RESULT_BRANCH"
  rm -rf "$RUNNER_TEMP/results-worktree/validation-results"
  mkdir -p "$RUNNER_TEMP/results-worktree/validation-results"
  cp -a "$RESULT_DIR"/. "$RUNNER_TEMP/results-worktree/validation-results/"
  cd "$RUNNER_TEMP/results-worktree"
  git add validation-results
  git commit -m "test: publish Oculus real shader validation results" || true
  git push origin "HEAD:$RESULT_BRANCH"
  exit "$code"
}
trap publish_results EXIT

rm -rf "$OCULUS_ROOT" "$MC_DIR" "$SERVER_DIR"
git clone --depth 1 --branch 1.12.2-dev https://github.com/dabrelity1/Oculus.git "$OCULUS_ROOT"
mkdir -p "$RUNNER_TEMP/previous"
gh run download 29326417270 --repo "$GITHUB_REPOSITORY" --name Oculus-1.12.2-production-continuation --dir "$RUNNER_TEMP/previous"
source_archive=$(find "$RUNNER_TEMP/previous" -name patched-source.tar.gz -type f | head -n 1)
test -n "$source_archive"
tar -xzf "$source_archive" -C "$PROJECT_DIR"

cd "$PROJECT_DIR"
python3 - <<'PY'
from pathlib import Path

mixin = Path('src/main/java/net/oculus/mixin/pipeline/ChunkOneshotGraphicsStateMixin.java')
text = mixin.read_text()
old = 'private void oculus$captureVertexFormat(CommandList commandList, ChunkMeshData meshData, CallbackInfo ci, VertexData vertexData, GlVertexFormat<ChunkMeshAttribute> vertexFormat, TessellationBinding[] bindings, GlMutableBuffer vertexBuffer)'
new = 'private void oculus$captureVertexFormat(CommandList commandList, ChunkMeshData meshData, CallbackInfo ci, VertexData vertexData, GlVertexFormat<ChunkMeshAttribute> vertexFormat)'
if old in text:
    text = text.replace(old, new, 1)
    text = text.replace('import me.jellysquid.mods.sodium.client.gl.buffer.GlMutableBuffer;\n', '')
    mixin.write_text(text)
elif new not in text:
    raise SystemExit('Unexpected ChunkOneshot callback signature')

build = Path('build.gradle')
gradle = build.read_text()
if 'configurations { oculusEmbed }' not in gradle:
    gradle = gradle.replace('dependencies {\n', 'configurations { oculusEmbed }\n\ndependencies {\n', 1)
    dependency_anchor = '    testCompile "junit:junit:4.13.2"\n'
    if dependency_anchor not in gradle:
        raise SystemExit('Dependency anchor not found')
    gradle = gradle.replace(
        dependency_anchor,
        dependency_anchor
        + '    oculusEmbed("org.anarres:jcpp:1.4.14") { transitive = false }\n'
        + '    oculusEmbed("org.slf4j:slf4j-api:1.7.12") { transitive = false }\n',
        1,
    )
    jar_anchor = 'jar {\n'
    if jar_anchor not in gradle:
        raise SystemExit('Jar task anchor not found')
    gradle = gradle.replace(
        jar_anchor,
        'jar {\n'
        '    duplicatesStrategy = DuplicatesStrategy.EXCLUDE\n'
        '    from { configurations.oculusEmbed.collect { zipTree(it) } }\n'
        '    exclude "META-INF/*.SF", "META-INF/*.RSA", "META-INF/*.DSA"\n',
        1,
    )
    build.write_text(gradle)
PY

chmod +x gradlew
status=1
set +e
for attempt in 1 2 3; do
  echo "=== BUILD ATTEMPT $attempt ==="
  ./gradlew --no-daemon --console=plain build -x test -x compileTestJava > build.log 2>&1
  status=$?
  tail -n 260 build.log
  if [ "$status" -eq 0 ]; then
    break
  fi
  sleep 10
done
set -e
test "$status" -eq 0
jar tf build/libs/oculus-0.1.0.jar | grep -q '^org/anarres/cpp/PreprocessorListener.class$'
jar tf build/libs/oculus-0.1.0.jar | grep -q '^org/slf4j/Logger.class$'
jar tf build/libs/oculus-0.1.0.jar | grep -q '^oculus.refmap.json$'

python3 -m pip install --quiet minecraft-launcher-lib
export MC_DIR SERVER_DIR OCULUS_JAR="$PROJECT_DIR/build/libs/oculus-0.1.0.jar"
python3 - <<'PY' > "$RUNNER_TEMP/install.log" 2>&1
import json
import os
import pathlib
import shutil
import urllib.request
import zipfile

import minecraft_launcher_lib


def download(url, path):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={'User-Agent': 'Oculus real shader validation'})
    with urllib.request.urlopen(request, timeout=180) as response, path.open('wb') as output:
        shutil.copyfileobj(response, output)


mc = pathlib.Path(os.environ['MC_DIR'])
server = pathlib.Path(os.environ['SERVER_DIR'])
mc.mkdir(parents=True, exist_ok=True)
server.mkdir(parents=True, exist_ok=True)
java = os.path.join(os.environ['JAVA_HOME'], 'bin', 'java')
forge = '1.12.2-14.23.5.2768'

minecraft_launcher_lib.install.install_minecraft_version('1.12.2', str(mc))
installer = mc / 'forge-installer.jar'
download(f'https://maven.minecraftforge.net/net/minecraftforge/forge/{forge}/forge-{forge}-installer.jar', installer)
with zipfile.ZipFile(installer) as archive:
    info = json.loads(archive.read('install_profile.json'))['versionInfo']
    version_id = info['id']
    version_dir = mc / 'versions' / version_id
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / f'{version_id}.json').write_text(json.dumps(info, indent=2))
    shutil.copy2(mc / 'versions/1.12.2/1.12.2.jar', version_dir / f'{version_id}.jar')
    forge_jar = mc / 'libraries/net/minecraftforge/forge' / forge / f'forge-{forge}.jar'
    forge_jar.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(f'forge-{forge}-universal.jar') as source, forge_jar.open('wb') as output:
        shutil.copyfileobj(source, output)
minecraft_launcher_lib.install.install_minecraft_version(version_id, str(mc))

mods = mc / 'mods'
mods.mkdir(exist_ok=True)
shutil.copy2(os.environ['OCULUS_JAR'], mods / 'oculus-0.1.0-real-shader-tested.jar')
download('https://repo.cleanroommc.com/releases/zone/rong/mixinbooter/11.5/mixinbooter-11.5.jar', mods / '-mixinbooter-11.5.jar')
download('https://api.modrinth.com/maven/maven/modrinth/relictium/1.2.0/relictium-1.2.0.jar', mods / 'relictium-1.2.0.jar')

pack = mc / 'shaderpacks' / 'OculusValidation' / 'shaders'
pack.mkdir(parents=True, exist_ok=True)
vertex = '''#version 120
varying vec2 texcoord;
varying vec2 lmcoord;
varying vec4 vcolor;
void main() {
    gl_Position = ftransform();
    texcoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    lmcoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;
    vcolor = gl_Color;
}
'''
fragment = '''#version 120
uniform sampler2D texture;
uniform sampler2D lightmap;
varying vec2 texcoord;
varying vec2 lmcoord;
varying vec4 vcolor;
/* DRAWBUFFERS:0 */
void main() {
    vec4 base = texture2D(texture, texcoord) * vcolor;
    vec3 light = texture2D(lightmap, lmcoord).rgb;
    gl_FragData[0] = vec4(base.rgb * max(light, vec3(0.18)), base.a);
}
'''
basic_fragment = '''#version 120
varying vec4 vcolor;
/* DRAWBUFFERS:0 */
void main() {
    gl_FragData[0] = vcolor;
}
'''
final_vertex = '''#version 120
varying vec2 texcoord;
void main() {
    gl_Position = ftransform();
    texcoord = gl_MultiTexCoord0.xy;
}
'''
final_fragment = '''#version 120
uniform sampler2D colortex0;
varying vec2 texcoord;
void main() {
    vec3 color = texture2D(colortex0, texcoord).rgb;
    gl_FragColor = vec4(color * vec3(1.08, 1.00, 0.92), 1.0);
}
'''
programs = [
    'gbuffers_textured', 'gbuffers_textured_lit', 'gbuffers_terrain',
    'gbuffers_water', 'gbuffers_entities', 'gbuffers_block',
    'gbuffers_hand', 'gbuffers_weather', 'gbuffers_skytextured'
]
for name in programs:
    (pack / f'{name}.vsh').write_text(vertex)
    (pack / f'{name}.fsh').write_text(fragment)
(pack / 'gbuffers_basic.vsh').write_text(vertex)
(pack / 'gbuffers_basic.fsh').write_text(basic_fragment)
(pack / 'final.vsh').write_text(final_vertex)
(pack / 'final.fsh').write_text(final_fragment)
(pack / 'shaders.properties').write_text('oldLighting=true\n')
config = mc / 'config'
config.mkdir(exist_ok=True)
(config / 'oculus.properties').write_text(
    'selectedPackName=OculusValidation\n'
    'shadersEnabled=true\n'
    'debugEnabled=true\n'
)

options = minecraft_launcher_lib.utils.generate_test_options()
options.update({
    'username': 'OculusShaderTest',
    'uuid': '00000000-0000-0000-0000-000000000002',
    'token': '0',
    'executablePath': java,
    'defaultExecutablePath': java,
    'gameDirectory': str(mc),
    'customResolution': True,
    'resolutionWidth': '1280',
    'resolutionHeight': '720',
    'jvmArguments': [
        '-Xms512m', '-Xmx3G', '-Duser.language=en',
        '-Doculus.validation.shaderPack=OculusValidation',
        '-Doculus.validation.exitAfterWorldTicks=240',
        '-Doculus.validation.screenshotWorldTick=160',
        '-Doculus.validation.worldTime=6000',
    ],
})
command = minecraft_launcher_lib.command.get_minecraft_command(version_id, str(mc), options)
command.extend(['--server', '127.0.0.1', '--port', '25565'])
(mc / 'launch-command.json').write_text(json.dumps(command))

manifest = json.loads(urllib.request.urlopen('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json').read())
version_url = next(version['url'] for version in manifest['versions'] if version['id'] == '1.12.2')
version_json = json.loads(urllib.request.urlopen(version_url).read())
download(version_json['downloads']['server']['url'], server / 'server.jar')
(server / 'eula.txt').write_text('eula=true\n')
(server / 'server.properties').write_text(
    'online-mode=false\n'
    'server-port=25565\n'
    'level-name=world\n'
    'view-distance=6\n'
    'spawn-protection=0\n'
    'motd=Oculus shader validation\n'
)
print('Client ready:', version_id, sorted(path.name for path in mods.iterdir()))
PY
cat "$RUNNER_TEMP/install.log"

cd "$SERVER_DIR"
java -Xms512m -Xmx1G -jar server.jar nogui > server.log 2>&1 &
server_pid=$!
echo "$server_pid" > server.pid
for attempt in $(seq 1 90); do
  if grep -q 'Done (' server.log; then
    break
  fi
  kill -0 "$server_pid" 2>/dev/null || { cat server.log; exit 1; }
  sleep 1
done
grep -q 'Done (' server.log

sudo apt-get update -qq
sudo apt-get install -y -qq xserver-xorg-video-dummy x11-xserver-utils mesa-utils imagemagick
cat > /tmp/xorg-dummy.conf <<'XORG'
Section "ServerFlags"
    Option "DontVTSwitch" "true"
    Option "AllowMouseOpenFail" "true"
    Option "PciForceNone" "true"
EndSection
Section "Device"
    Identifier "DummyDevice"
    Driver "dummy"
    VideoRam 256000
EndSection
Section "Monitor"
    Identifier "DummyMonitor"
    HorizSync 5.0-1000.0
    VertRefresh 5.0-200.0
    Modeline "1280x720" 74.50 1280 1344 1472 1664 720 723 728 748
EndSection
Section "Screen"
    Identifier "DummyScreen"
    Device "DummyDevice"
    Monitor "DummyMonitor"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "1280x720"
        Virtual 1280 720
    EndSubSection
EndSection
XORG
sudo Xorg :99 -noreset -ac +extension GLX +extension RANDR -config /tmp/xorg-dummy.conf > /tmp/xorg.log 2>&1 &
xorg_pid=$!
sleep 4
export DISPLAY=:99
export LIBGL_ALWAYS_SOFTWARE=1
glxinfo -B

python3 - <<'PY'
import json
import os
import pathlib
import shlex
mc = pathlib.Path(os.environ['MC_DIR'])
command = json.loads((mc / 'launch-command.json').read_text())
(mc / 'run.sh').write_text('#!/bin/sh\nexec ' + ' '.join(shlex.quote(part) for part in command) + '\n')
os.chmod(mc / 'run.sh', 0o755)
PY

set +e
timeout 240s "$MC_DIR/run.sh" > "$MC_DIR/shader-runtime.log" 2>&1
client_status=$?
set -e
kill "$server_pid" 2>/dev/null || true
sudo kill "$xorg_pid" 2>/dev/null || true

echo "Client exit status: $client_status"
tail -n 1200 "$MC_DIR/shader-runtime.log"
test -f "$MC_DIR/logs/latest.log" && tail -n 1200 "$MC_DIR/logs/latest.log"
tail -n 250 "$SERVER_DIR/server.log"

fatal='NoClassDefFoundError|ClassNotFoundException: org.anarres|Failed to load configured shader pack|Failed to create shader rendering pipeline|Shader compilation failed|ProgramLoadException|Game crashed|Unexpected error|MixinTransformerError|InjectionError'
if grep -Eqi "$fatal" "$MC_DIR/shader-runtime.log" "$MC_DIR/logs/latest.log" 2>/dev/null; then
  echo 'Fatal shader validation pattern found.'
  exit 1
fi
grep -q 'Using runtime validation shader pack override: OculusValidation' "$MC_DIR/shader-runtime.log" "$MC_DIR/logs/latest.log"
grep -q 'Using configured shader pack: OculusValidation' "$MC_DIR/shader-runtime.log" "$MC_DIR/logs/latest.log"
grep -q 'Creating pipeline for dimension minecraft:overworld: ShaderWorldRenderingPipeline' "$MC_DIR/shader-runtime.log" "$MC_DIR/logs/latest.log"
grep -q 'OculusShaderTest.*joined the game' "$SERVER_DIR/server.log"
grep -q 'Oculus runtime validation captured post-world-render screenshot' "$MC_DIR/shader-runtime.log" "$MC_DIR/logs/latest.log"
screenshot=$(find "$MC_DIR/screenshots" -maxdepth 1 -type f -name '*.png' | sort | tail -n 1)
test -s "$screenshot"
mean=$(convert "$screenshot" -colorspace gray -format '%[fx:mean]' info:)
printf '%s\n' "$mean" | tee "$RESULT_DIR/screenshot-mean.txt"
python3 - "$mean" <<'PY'
import sys
mean = float(sys.argv[1])
if mean <= 0.005:
    raise SystemExit('Rendered screenshot is effectively black')
PY
if [ "$client_status" -ne 0 ]; then
  echo "Client did not exit cleanly: $client_status"
  exit 1
fi

echo 'Oculus real shader validation passed.' | tee "$RESULT_DIR/summary.txt"
