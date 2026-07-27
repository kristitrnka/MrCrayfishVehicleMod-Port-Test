from pathlib import Path
import json
R=Path('.')
items=[
('rocking_chair_black','Rocking Chair Black','chair','minecraft:block/dark_oak_planks'),('rocking_chair_medium','Rocking Chair Medium','chair','minecraft:block/oak_planks'),('wooden_chair_beach','Wooden Chair Beach','chair','minecraft:block/birch_planks'),('borje_chair_black','Borje Chair Black','chair','minecraft:block/black_wool'),('ingolf_chair_light','Ingolf Chair Light','chair','minecraft:block/smooth_quartz'),('wooden_table_dark','Wooden Table Dark','table','minecraft:block/dark_oak_planks'),('wooden_table_black','Wooden Table Black','table','minecraft:block/black_concrete'),('wooden_table_medium','Wooden Table Medium','table','minecraft:block/spruce_planks'),('restaurant_table_coral','Restaurant Table Coral','table','minecraft:block/orange_terracotta'),('tv_stand_dark','TV Stand Dark','stand','minecraft:block/dark_oak_planks'),('industrial_tv_stand_medium','Industrial TV Stand Medium','stand','minecraft:block/iron_block'),('short_bookshelf_black','Short Bookshelf Black','shelf','minecraft:block/black_concrete'),('short_bookshelf_dark','Short Bookshelf Dark Wood','shelf','minecraft:block/dark_oak_planks'),('dresser_medium','Dresser Medium','cabinet','minecraft:block/spruce_planks'),('filing_cabinet_medium','Filing Cabinet Medium','cabinet','minecraft:block/iron_block'),('bowl_sink_medium','Bowl Sink Medium','sink','minecraft:block/smooth_quartz'),('vanity_beach','Vanity Beach','cabinet','minecraft:block/birch_planks'),('lava_lamp_green','Lava Lamp Green','lamp','minecraft:block/lime_stained_glass'),('lava_lamp_rainbow','Lava Lamp Rainbow','lamp','minecraft:block/magenta_stained_glass'),('lamp_cyan','Lamp Cyan','lamp','minecraft:block/cyan_stained_glass')]
presets={'chair':[(2,0,2,14,3,14),(3,3,3,13,9,13),(2,9,12,14,16,14),(2,0,2,4,10,4),(12,0,2,14,10,4),(2,0,12,4,10,14),(12,0,12,14,10,14)],'table':[(1,12,1,15,16,15),(2,0,2,4,12,4),(12,0,2,14,12,4),(2,0,12,4,12,14),(12,0,12,14,12,14)],'stand':[(1,0,2,15,4,14),(2,4,3,14,12,13),(1,12,2,15,16,14),(7,4,2,9,12,3)],'shelf':[(1,0,2,15,16,14),(2,3,1,14,5,15),(2,8,1,14,10,15),(2,13,1,14,15,15)],'cabinet':[(1,0,2,15,16,14),(2,2,1,14,5,15),(2,6,1,14,9,15),(2,10,1,14,13,15)],'sink':[(1,0,2,15,10,14),(2,10,1,14,13,15),(4,12,4,12,15,12),(7,13,7,9,16,9)],'lamp':[(6,0,6,10,2,10),(7,2,7,9,11,9),(4,10,4,12,16,12)]}
def w(p,s):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
w('settings.gradle',"pluginManagement { repositories { gradlePluginPortal(); maven { url='https://maven.neoforged.net/releases' }; mavenCentral() } }\nrootProject.name='decocraftport'\n")
w('gradle.properties',"org.gradle.jvmargs=-Xmx2G\norg.gradle.daemon=false\norg.gradle.configuration-cache=false\nminecraft_version=1.21.1\nneo_version=21.1.244\nmod_id=decocraftport\nmod_name=Decocraft Port\nmod_version=0.3.0-20models\nmod_group_id=com.kristihack.decocraftport\n")
w('build.gradle',"""plugins { id 'java-library'; id 'net.neoforged.gradle.userdev' version '7.1.38' }
version=mod_version
group=mod_group_id
base { archivesName=mod_id }
java.toolchain.languageVersion=JavaLanguageVersion.of(21)
repositories { mavenCentral() }
dependencies { implementation \"net.neoforged:neoforge:${neo_version}\" }
tasks.withType(ProcessResources).configureEach { filesMatching('META-INF/neoforge.mods.toml') { expand mod_id:mod_id,mod_name:mod_name,mod_version:mod_version,neo_version:neo_version } }
tasks.withType(JavaCompile).configureEach { options.encoding='UTF-8' }
""")
w('src/main/resources/META-INF/neoforge.mods.toml',"""modLoader=\"javafml\"
loaderVersion=\"[1,)\"
license=\"All Rights Reserved\"
[[mods]]
modId=\"${mod_id}\"
version=\"${mod_version}\"
displayName=\"${mod_name}\"
description='''20-model Decocraft 1.21.1 port build.'''
[[dependencies.${mod_id}]]
modId=\"neoforge\"
type=\"required\"
versionRange=\"[${neo_version},)\"
ordering=\"NONE\"
side=\"BOTH\"
[[dependencies.${mod_id}]]
modId=\"minecraft\"
type=\"required\"
versionRange=\"[1.21.1,1.22)\"
ordering=\"NONE\"
side=\"BOTH\"
""")
regs='\n'.join(f'    public static final DeferredBlock<FurnitureBlock> {n.upper()} = furniture("{n}");' for n,_,_,_ in items)
iregs='\n'.join(f'    public static final DeferredItem<BlockItem> {n.upper()}_ITEM = ITEMS.register("{n}", () -> new BlockItem({n.upper()}.get(), new Item.Properties()));' for n,_,_,_ in items)
outs='\n'.join(f'                output.accept({n.upper()}_ITEM.get());' for n,_,_,_ in items)
w('src/main/java/com/kristihack/decocraftport/DecocraftPort.java',f'''package com.kristihack.decocraftport;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.*;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.registries.*;
@Mod(DecocraftPort.MOD_ID)
public final class DecocraftPort {{
 public static final String MOD_ID="decocraftport";
 public static final DeferredRegister.Blocks BLOCKS=DeferredRegister.createBlocks(MOD_ID);
 public static final DeferredRegister.Items ITEMS=DeferredRegister.createItems(MOD_ID);
 public static final DeferredRegister<CreativeModeTab> TABS=DeferredRegister.create(Registries.CREATIVE_MODE_TAB,MOD_ID);
{regs}
{iregs}
 private static DeferredBlock<FurnitureBlock> furniture(String n){{return BLOCKS.register(n,()->new FurnitureBlock(BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(1.2F).sound(SoundType.WOOD).noOcclusion()));}}
 public static final DeferredHolder<CreativeModeTab,CreativeModeTab> TAB=TABS.register("decocraft",()->CreativeModeTab.builder().title(Component.translatable("itemGroup.decocraftport")).icon(()->ROCKING_CHAIR_BLACK_ITEM.get().getDefaultInstance()).displayItems((p,output)->{{
{outs}
 }}).build());
 public DecocraftPort(IEventBus bus,ModContainer container){{BLOCKS.register(bus);ITEMS.register(bus);TABS.register(bus);}}
}}
''')
w('src/main/java/com/kristihack/decocraftport/FurnitureBlock.java','''package com.kristihack.decocraftport;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.state.*;
public final class FurnitureBlock extends HorizontalDirectionalBlock {
 public static final MapCodec<FurnitureBlock> CODEC=simpleCodec(FurnitureBlock::new);
 public FurnitureBlock(Properties p){super(p);registerDefaultState(stateDefinition.any().setValue(FACING,Direction.NORTH));}
 @Override protected MapCodec<? extends HorizontalDirectionalBlock> codec(){return CODEC;}
 @Override public BlockState getStateForPlacement(BlockPlaceContext c){return defaultBlockState().setValue(FACING,c.getHorizontalDirection().getOpposite());}
 @Override protected BlockState rotate(BlockState s,Rotation r){return s.setValue(FACING,r.rotate(s.getValue(FACING)));}
 @Override protected BlockState mirror(BlockState s,Mirror m){return s.rotate(m.getRotation(s.getValue(FACING)));}
 @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block,BlockState> b){b.add(FACING);}
}
''')
lang={'itemGroup.decocraftport':'Decocraft Port'}
for n,label,kind,tex in items:
 lang[f'block.decocraftport.{n}']=label
 variants={f'facing={d}':{'model':f'decocraftport:block/{n}',**({} if d=='north' else {'y':{'east':90,'south':180,'west':270}[d]})} for d in ['north','east','south','west']}
 w(f'src/main/resources/assets/decocraftport/blockstates/{n}.json',json.dumps({'variants':variants},indent=2))
 elements=[]
 for a,b,c,d,e,f in presets[kind]:
  elements.append({'from':[a,b,c],'to':[d,e,f],'faces':{q:{'texture':'#all'} for q in ['north','south','east','west','up','down']}})
 w(f'src/main/resources/assets/decocraftport/models/block/{n}.json',json.dumps({'ambientocclusion':True,'textures':{'all':tex,'particle':tex},'elements':elements},indent=2))
 w(f'src/main/resources/assets/decocraftport/models/item/{n}.json',json.dumps({'parent':f'decocraftport:block/{n}'},indent=2))
 w(f'src/main/resources/data/decocraftport/loot_table/blocks/{n}.json',json.dumps({'type':'minecraft:block','pools':[{'rolls':1,'entries':[{'type':'minecraft:item','name':f'decocraftport:{n}'}],'conditions':[{'condition':'minecraft:survives_explosion'}]}]},indent=2))
 w(f'src/main/resources/data/decocraftport/recipe/{n}.json',json.dumps({'type':'minecraft:crafting_shaped','category':'decorations','pattern':['PPP',' S ','S S'],'key':{'P':{'item':'minecraft:oak_planks'},'S':{'item':'minecraft:stick'}},'result':{'id':f'decocraftport:{n}','count':1}},indent=2))
w('src/main/resources/assets/decocraftport/lang/en_us.json',json.dumps(lang,indent=2))
print('Generated 20-model Decocraft project')
