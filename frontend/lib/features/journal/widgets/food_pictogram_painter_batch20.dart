import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch20Ids=<String>{'omani_shuwa','dhofari_madhbi','dhofari_maajeen'};
bool hasCodeFoodPictogramBatch20(String foodId)=>codeFoodPictogramBatch20Ids.contains(foodId);
class FoodPictogramPainterBatch20 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch20(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,78,60,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'omani_shuwa':c.drawOval(const Rect.fromLTWH(21,55,58,22),f(const Color(0xFFD6B36A)));c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(31,37,38,29),const Radius.circular(12)),f(const Color(0xFF7B4632)));c.drawLine(const Offset(38,45),const Offset(60,58),s(const Color(0xFFD8A06A),3));break;case 'dhofari_madhbi':for(final y in <double>[61,67,73])c.drawOval(Rect.fromCenter(center:Offset(50,y),width:55,height:9),f(const Color(0xFF6E6258)));c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(31,35,38,28),const Radius.circular(10)),f(const Color(0xFF8B4D32)));c.drawLine(const Offset(35,43),const Offset(63,55),s(const Color(0xFFD49A5D),3));break;case 'dhofari_maajeen':c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(25,43,50,31),const Radius.circular(8)),f(const Color(0xFFB88955)));for(final r in <Rect>[Rect.fromLTWH(31,48,13,8),Rect.fromLTWH(47,55,14,9),Rect.fromLTWH(58,46,11,8)])c.drawRRect(RRect.fromRectAndRadius(r,const Radius.circular(3)),f(const Color(0xFF75422E)));break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch20 o)=>o.foodId!=foodId;
}
