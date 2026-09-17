import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch19Ids=<String>{'qatari_saloona','qatari_margoog','qatari_sago'};
bool hasCodeFoodPictogramBatch19(String foodId)=>codeFoodPictogramBatch19Ids.contains(foodId);
class FoodPictogramPainterBatch19 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch19(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,77,60,7)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'qatari_saloona':c.drawOval(const Rect.fromLTWH(20,42,60,35),f(const Color(0xFF5E8E87)));c.drawOval(const Rect.fromLTWH(25,37,50,29),f(const Color(0xFFB94D3D)));for(final p in <Offset>[Offset(38,48),Offset(51,54),Offset(63,46)])c.drawCircle(p,4,f(const Color(0xFFD6A24D)));break;case 'qatari_margoog':c.drawOval(const Rect.fromLTWH(20,42,60,35),f(const Color(0xFF718F87)));c.drawOval(const Rect.fromLTWH(25,37,50,29),f(const Color(0xFF9A633B)));for(final r in <Rect>[Rect.fromLTWH(34,45,10,6),Rect.fromLTWH(48,52,11,6),Rect.fromLTWH(59,43,9,6)])c.drawRRect(RRect.fromRectAndRadius(r,const Radius.circular(2)),f(const Color(0xFFE0BD79)));break;case 'qatari_sago':c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(28,34,44,43),const Radius.circular(9)),f(const Color(0xFFB54D57)));c.drawOval(const Rect.fromLTWH(31,31,38,13),f(const Color(0xFFD96A72)));for(final p in <Offset>[Offset(39,49),Offset(49,57),Offset(60,48),Offset(58,65),Offset(42,67)])c.drawCircle(p,2.4,f(const Color(0xFFF0C58A)));break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch19 o)=>o.foodId!=foodId;
}
