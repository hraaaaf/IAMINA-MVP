import 'package:flutter/material.dart';

import '../../../core/data/food_pictogram_registry.dart';
import '../../../core/data/meal_food_catalog.dart';
import '../../../core/theme/app_theme.dart';
import 'food_pictogram_painter.dart';
import 'food_pictogram_painter_batch2.dart';
import 'food_pictogram_painter_batch3.dart';
import 'food_pictogram_painter_batch4.dart';
import 'food_pictogram_painter_batch5.dart';
import 'food_pictogram_painter_batch6.dart';
import 'food_pictogram_painter_batch7.dart';
import 'food_pictogram_painter_batch8.dart';
import 'food_pictogram_painter_batch9.dart';
import 'food_pictogram_painter_batch10.dart';
import 'food_pictogram_painter_batch11.dart';
import 'food_pictogram_painter_batch12.dart';
import 'food_pictogram_painter_batch13.dart';
import 'food_pictogram_painter_batch14.dart';
import 'food_pictogram_painter_batch15.dart';
import 'food_pictogram_painter_batch16.dart';
import 'food_pictogram_painter_batch17.dart';
import 'food_pictogram_painter_batch18.dart';

class FoodPictogram extends StatelessWidget {
  final MealFoodItem item;
  final double size;
  final bool selected;
  const FoodPictogram({super.key,required this.item,this.size=42,this.selected=false});
  String get assetPath=>certifiedFoodPictogramPath(item.pictogramKey);
  Widget _emojiFallback()=>ExcludeSemantics(child:Text(item.visual,style:TextStyle(fontSize:size*.48,height:1)));
  Widget _nativePictogram(){final key=item.pictogramKey;final CustomPainter painter;if(hasCodeFoodPictogramBatch18(key)){painter=FoodPictogramPainterBatch18(key);}else if(hasCodeFoodPictogramBatch17(key)){painter=FoodPictogramPainterBatch17(key);}else if(hasCodeFoodPictogramBatch16(key)){painter=FoodPictogramPainterBatch16(key);}else if(hasCodeFoodPictogramBatch15(key)){painter=FoodPictogramPainterBatch15(key);}else if(hasCodeFoodPictogramBatch14(key)){painter=FoodPictogramPainterBatch14(key);}else if(hasCodeFoodPictogramBatch13(key)){painter=FoodPictogramPainterBatch13(key);}else if(hasCodeFoodPictogramBatch12(key)){painter=FoodPictogramPainterBatch12(key);}else if(hasCodeFoodPictogramBatch11(key)){painter=FoodPictogramPainterBatch11(key);}else if(hasCodeFoodPictogramBatch10(key)){painter=FoodPictogramPainterBatch10(key);}else if(hasCodeFoodPictogramBatch9(key)){painter=FoodPictogramPainterBatch9(key);}else if(hasCodeFoodPictogramBatch8(key)){painter=FoodPictogramPainterBatch8(key);}else if(hasCodeFoodPictogramBatch7(key)){painter=FoodPictogramPainterBatch7(key);}else if(hasCodeFoodPictogramBatch6(key)){painter=FoodPictogramPainterBatch6(key);}else if(hasCodeFoodPictogramBatch5(key)){painter=FoodPictogramPainterBatch5(key);}else if(hasCodeFoodPictogramBatch4(key)){painter=FoodPictogramPainterBatch4(key);}else if(hasCodeFoodPictogramBatch3(key)){painter=FoodPictogramPainterBatch3(key);}else if(hasCodeFoodPictogramBatch2(key)){painter=FoodPictogramPainterBatch2(key);}else{painter=FoodPictogramPainter(key);}return ExcludeSemantics(child:CustomPaint(size:Size.square(size),painter:painter));}
  @override Widget build(BuildContext context){final accent=AminaTheme.accent(context);final certified=hasCertifiedFoodPictogram(item.pictogramKey);final native=hasCodeFoodPictogram(item.pictogramKey)||hasCodeFoodPictogramBatch2(item.pictogramKey)||hasCodeFoodPictogramBatch3(item.pictogramKey)||hasCodeFoodPictogramBatch4(item.pictogramKey)||hasCodeFoodPictogramBatch5(item.pictogramKey)||hasCodeFoodPictogramBatch6(item.pictogramKey)||hasCodeFoodPictogramBatch7(item.pictogramKey)||hasCodeFoodPictogramBatch8(item.pictogramKey)||hasCodeFoodPictogramBatch9(item.pictogramKey)||hasCodeFoodPictogramBatch10(item.pictogramKey)||hasCodeFoodPictogramBatch11(item.pictogramKey)||hasCodeFoodPictogramBatch12(item.pictogramKey)||hasCodeFoodPictogramBatch13(item.pictogramKey)||hasCodeFoodPictogramBatch14(item.pictogramKey)||hasCodeFoodPictogramBatch15(item.pictogramKey)||hasCodeFoodPictogramBatch16(item.pictogramKey)||hasCodeFoodPictogramBatch17(item.pictogramKey)||hasCodeFoodPictogramBatch18(item.pictogramKey);return Semantics(image:true,label:item.plainLabelFor(Localizations.localeOf(context)),child:Container(width:size,height:size,decoration:BoxDecoration(color:selected?accent.withValues(alpha:AminaTheme.isDark(context) ? .18 : .09):AminaTheme.subtleBg(context),borderRadius:BorderRadius.circular(size*.31),border:Border.all(color:selected?accent.withValues(alpha:.45):AminaTheme.divider(context))),clipBehavior:Clip.antiAlias,alignment:Alignment.center,child:certified?Image.asset(assetPath,width:size,height:size,fit:BoxFit.contain,excludeFromSemantics:true,errorBuilder:(context,error,stackTrace)=>native?_nativePictogram():_emojiFallback()):native?_nativePictogram():_emojiFallback()));}
}
