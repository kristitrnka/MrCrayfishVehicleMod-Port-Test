from pathlib import Path
import json, shutil
R=Path('.')
items=[
 ('wooden_chair','Wooden Chair','chair','minecraft:block/oak_planks'),
 ('modern_chair','Modern Chair','chair','minecraft:block/smooth_quartz'),
 ('coffee_table','Coffee Table','table','minecraft:block/spruce_planks'),
 ('tv_stand','TV Stand','stand','minecraft:block/dark_oak_planks'),
 ('floor_lamp','Floor Lamp','lamp','minecraft:block/yellow_stained_glass')]
presets={
 'chair':[(2,0,2,14,3,14),(3,3,3,13,9,13),(2,9,12,14,16,14),(2,0,2,4,10,4),(12,0,2,14,10,4),(2,0,12,4,10,14),(12,0,12,14,10,14)],
 'table':[(1,9,1,15,12,15),(2,0,2,4,9,4),(12,0,2,14,9,4),(2,0,12,4,9,14),(12,0,12,14,9,14)],
 'stand':[(1,0,2,15,4,14),(2,4,3,14,11,13),(1,11,2,15,14,14),(7,4,2,9,11,3)],
 'lamp':[(5,0,5,11,2,11),(7,2,7,9,11,9),(3,10,3,13,16,13)]}
def w(path,text):
 p=R/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
# Keep the official 26.2 MDK build scripts, only replace metadata and mod sources.
gp=(R/'gradle.properties').read_text()
for old,new in [('mod_id=examplemod','mod_id=mkfurniture'),('mod_name=Example Mod','mod_name=M&K Furniture'),('mod_version=1.0.0','mod_version=0.1.0'),('mod_group_id=com.example.examplemod','mod_group_id=com.kristihack.mkfurniture')]: gp=gp.replace(old,new)
w('gradle.properties',gp)
shutil.rmtree(R/'src/main/java/com/example',ignore_errors=True)
shutil.rmtree(R/'src/main/resources/assets/examplemod',ignore_errors=True)
regs='\n'.join(f'''    public static final DeferredBlock<FurnitureBlock> {n.upper()} = BLOCKS.register("{n}", id -> new FurnitureBlock(BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id)).strength(1.2F).sound(SoundType.WOOD).noOcclusion()));\n    public static final DeferredItem<BlockItem> {n.upper()}_ITEM = ITEMS.registerSimpleBlockItem("{n}", {n.upper()});''' for n,_,_,_ in items)
outs='\n'.join(f'                output.accept({n.upper()}_ITEM.get());' for n,_,_,_ in items)
w('src/main/java/com/kristihack/mkfurniture/MKFurniture.java',f'''package com.kristihack.mkfurniture;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.registries.*;
@Mod(MKFurniture.MOD_ID)
public final class MKFurniture {{
    public static final String MOD_ID="mkfurniture";
    public static final DeferredRegister.Blocks BLOCKS=DeferredRegister.createBlocks(MOD_ID);
    public static final DeferredRegister.Items ITEMS=DeferredRegister.createItems(MOD_ID);
    public static final DeferredRegister<CreativeModeTab> TABS=DeferredRegister.create(Registries.CREATIVE_MODE_TAB,MOD_ID);
{regs}
    public static final DeferredHolder<CreativeModeTab,CreativeModeTab> TAB=TABS.register("furniture",()->CreativeModeTab.builder()
        .title(Component.translatable("itemGroup.mkfurniture"))
        .withTabsBefore(CreativeModeTabs.FUNCTIONAL_BLOCKS)
        .icon(()->WOODEN_CHAIR_ITEM.get().getDefaultInstance())
        .displayItems((parameters,output)->{{
{outs}
        }}).build());
    public MKFurniture(IEventBus bus, ModContainer container){{BLOCKS.register(bus);ITEMS.register(bus);TABS.register(bus);}}
}}
''')
w('src/main/java/com/kristihack/mkfurniture/FurnitureBlock.java','''package com.kristihack.mkfurniture;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.state.*;
public final class FurnitureBlock extends HorizontalDirectionalBlock {
    public static final MapCodec<FurnitureBlock> CODEC=simpleCodec(FurnitureBlock::new);
    public FurnitureBlock(Properties properties){super(properties);registerDefaultState(stateDefinition.any().setValue(FACING,Direction.NORTH));}
    @Override protected MapCodec<? extends HorizontalDirectionalBlock> codec(){return CODEC;}
    @Override public BlockState getStateForPlacement(BlockPlaceContext context){return defaultBlockState().setValue(FACING,context.getHorizontalDirection().getOpposite());}
    @Override protected BlockState rotate(BlockState state,Rotation rotation){return state.setValue(FACING,rotation.rotate(state.getValue(FACING)));}
    @Override protected BlockState mirror(BlockState state,Mirror mirror){return state.rotate(mirror.getRotation(state.getValue(FACING)));}
    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block,BlockState> builder){builder.add(FACING);}
}
''')
# Replace TOML values using MDK placeholders, preserving official format.
toml=R/'src/main/resources/META-INF/neoforge.mods.toml'
if toml.exists():
 t=toml.read_text().replace('examplemod','mkfurniture').replace('Example Mod','M&K Furniture')
 toml.write_text(t)
lang={'itemGroup.mkfurniture':'M&K Furniture'}
for n,label,kind,tex in items:
 lang[f'block.mkfurniture.{n}']=label
 variants={}
 for d,y in [('north',0),('east',90),('south',180),('west',270)]:
  v={'model':f'mkfurniture:block/{n}'}
  if y:v['y']=y
  variants[f'facing={d}']=v
 w(f'src/main/resources/assets/mkfurniture/blockstates/{n}.json',json.dumps({'variants':variants},indent=2))
 elements=[]
 for a,b,c,d,e,f in presets[kind]:
  elements.append({'from':[a,b,c],'to':[d,e,f],'faces':{q:{'texture':'#all'} for q in ['north','south','east','west','up','down']}})
 w(f'src/main/resources/assets/mkfurniture/models/block/{n}.json',json.dumps({'ambientocclusion':True,'textures':{'all':tex,'particle':tex},'elements':elements},indent=2))
 w(f'src/main/resources/assets/mkfurniture/models/item/{n}.json',json.dumps({'parent':f'mkfurniture:block/{n}'},indent=2))
 w(f'src/main/resources/data/mkfurniture/loot_table/blocks/{n}.json',json.dumps({'type':'minecraft:block','pools':[{'rolls':1,'entries':[{'type':'minecraft:item','name':f'mkfurniture:{n}'}],'conditions':[{'condition':'minecraft:survives_explosion'}]}]},indent=2))
w('src/main/resources/assets/mkfurniture/lang/en_us.json',json.dumps(lang,indent=2))
w('src/main/resources/assets/mkfurniture/lang/cs_cz.json',json.dumps(lang,indent=2,ensure_ascii=False))
print('Generated M&K Furniture 26.2 with 5 rotating models')
