import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch32Ids=<String>{'sudanese_kisra','sudanese_aseeda','sudanese_gurraasa'};
bool hasCodeFoodPictogramBatch32(String foodId)=>codeFoodPictogramBatch32Ids.contains(foodId);

class FoodPictogramPainterBatch32 extends CustomPainter{
  final String foodId;
  const FoodPictogramPainterBatch32(this.foodId);
  Paint f(Color c)=>Paint()..color=c..isAntiAlias=true;
  Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
  @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(17,78,66,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'sudanese_kisra':c.drawOval(const Rect.fromLTWH(17,44,66,30),f(const Color(0xFFD6A35F)));c.drawOval(const Rect.fromLTWH(22,40,56,27),f(const Color(0xFFE8C98B)));for(final p in <Offset>[Offset(31,49),Offset(43,55),Offset(55,47),Offset(67,55)]) c.drawCircle(p,1.8,f(const Color(0xFFB77B3E)));c.drawArc(const Rect.fromLTWH(27,43,46,20),.2,2.5,false,s(const Color(0xFFC28A4C),2));break;case 'sudanese_aseeda':c.drawOval(const Rect.fromLTWH(19,51,62,25),f(const Color(0xFF9A633E)));c.drawOval(const Rect.fromLTWH(25,39,50,31),f(const Color(0xFFD9B16D)));c.drawOval(const Rect.fromLTWH(39,47,22,12),f(const Color(0xFF7A4B2D)));c.drawCircle(const Offset(50,53),5,f(const Color(0xFFB36A35)));break;case 'sudanese_gurraasa':c.drawOval(const Rect.fromLTWH(17,48,66,27),f(const Color(0xFFA86B3D)));c.drawOval(const Rect.fromLTWH(21,40,58,30),f(const Color(0xFFE1B36D)));for(final p in <Offset>[Offset(31,49),Offset(42,45),Offset(54,53),Offset(66,47)]) c.drawCircle(p,2.2,f(const Color(0xFFB97842)));c.drawArc(const Rect.fromLTWH(26,43,48,22),.1,2.8,false,s(const Color(0xFFCA8C4C),2));break;}c.restore();}
  @override bool shouldRepaint(covariant FoodPictogramPainterBatch32 o)=>o.foodId!=foodId;
}
