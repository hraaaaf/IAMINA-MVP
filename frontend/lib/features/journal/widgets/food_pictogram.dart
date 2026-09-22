import 'package:flutter/material.dart';
import '../../../core/data/food_pictogram_registry.dart';
import '../../../core/data/meal_food_catalog.dart';
import '../../../core/theme/app_theme.dart';
import 'food_pictogram_native_dispatch.dart';

class FoodPictogram extends StatelessWidget {
  final MealFoodItem item;
  final double size;
  final bool selected;
  const FoodPictogram({super.key,required this.item,this.size=42,this.selected=false});
  String get assetPath=>certifiedFoodPictogramPath(item.pictogramKey);
  Widget _emojiFallback()=>ExcludeSemantics(child:Text(item.visual,style:TextStyle(fontSize:size*.48,height:1)));
  Widget _nativePictogram(){final painter=nativeFoodPictogramPainter(item.pictogramKey);return painter==null?_emojiFallback():ExcludeSemantics(child:CustomPaint(size:Size.square(size),painter:painter));}
  @override Widget build(BuildContext context){final accent=AminaTheme.accent(context);final certified=hasCertifiedFoodPictogram(item.pictogramKey);final native=hasNativeFoodPictogram(item.pictogramKey);return Semantics(image:true,label:item.plainLabelFor(Localizations.localeOf(context)),child:Container(width:size,height:size,decoration:BoxDecoration(color:selected?accent.withValues(alpha:AminaTheme.isDark(context)?.18:.09):AminaTheme.subtleBg(context),borderRadius:BorderRadius.circular(size*.31),border:Border.all(color:selected?accent.withValues(alpha:.45):AminaTheme.divider(context))),clipBehavior:Clip.antiAlias,alignment:Alignment.center,child:certified?Image.asset(assetPath,width:size,height:size,fit:BoxFit.contain,excludeFromSemantics:true,errorBuilder:(context,error,stackTrace)=>native?_nativePictogram():_emojiFallback()):native?_nativePictogram():_emojiFallback()));}
}
