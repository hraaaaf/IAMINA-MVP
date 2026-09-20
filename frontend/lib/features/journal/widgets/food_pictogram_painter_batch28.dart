import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch28Ids=<String>{'moroccan_pastilla','marrakech_tanjia','moroccan_mrouzia'};
bool hasCodeFoodPictogramBatch28(String foodId)=>codeFoodPictogramBatch28Ids.contains(foodId);
class FoodPictogramPainterBatch28 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch28(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,78,60,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'moroccan_pastilla':c.drawCircle(const Offset(50,58),27,f(const Color(0xFFD7A85B)));c.drawCircle(const Offset(50,56),23,f(const Color(0xFFF2D89A)));c.drawLine(const Offset(32,43),const Offset(68,69),s(const Color(0xFF9A653D),3));c.drawLine(const Offset(68,43),const Offset(32,69),s(const Color(0xFF9A653D),3));break;case 'marrakech_tanjia':c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(35,28,30,50),const Radius.circular(12)),f(const Color(0xFFB86E45)));c.drawRect(const Rect.fromLTWH(42,23,16,9),f(const Color(0xFF8E5137)));c.drawPath(Path()..moveTo(40,52)..quadraticBezierTo(50,44,60,52)..quadraticBezierTo(50,61,40,52),f(const Color(0xFFD89A55)));break;case 'moroccan_mrouzia':c.drawOval(const Rect.fromLTWH(18,50,64,28),f(const Color(0xFF8B5B3E)));c.drawOval(const Rect.fromLTWH(23,48,54,22),f(const Color(0xFF9D633A)));for(final p in <Offset>[Offset(33,55),Offset(43,63),Offset(55,55),Offset(66,62)])c.drawOval(Rect.fromCenter(center:p,width:8,height:5),f(const Color(0xFF4E342E)));for(final p in <Offset>[Offset(38,58),Offset(59,61)])c.drawCircle(p,4,f(const Color(0xFFD7B56D)));break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch28 o)=>o.foodId!=foodId;
}
