import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch33Ids=<String>{'palestinian_musakhan','palestinian_qidreh','jerusalem_kaak'};
bool hasCodeFoodPictogramBatch33(String foodId)=>codeFoodPictogramBatch33Ids.contains(foodId);

class FoodPictogramPainterBatch33 extends CustomPainter{
  final String foodId;
  const FoodPictogramPainterBatch33(this.foodId);
  Paint f(Color c)=>Paint()..color=c..isAntiAlias=true;
  Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
  @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(15,79,70,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'palestinian_musakhan':c.drawOval(const Rect.fromLTWH(15,53,70,24),f(const Color(0xFFD6A15B)));c.drawOval(const Rect.fromLTWH(20,48,60,22),f(const Color(0xFFE5BF7A)));c.drawOval(const Rect.fromLTWH(31,38,38,24),f(const Color(0xFF9A5537)));c.drawArc(const Rect.fromLTWH(27,44,46,19),.1,2.7,false,s(const Color(0xFF7C3E31),3));for(final p in <Offset>[Offset(27,55),Offset(38,51),Offset(63,53),Offset(72,58)])c.drawCircle(p,1.7,f(const Color(0xFF7E2F32)));break;case 'palestinian_qidreh':c.drawOval(const Rect.fromLTWH(19,55,62,22),f(const Color(0xFF8B5A3C)));c.drawRect(const Rect.fromLTWH(22,45,56,20),f(const Color(0xFFC98D4D)));c.drawOval(const Rect.fromLTWH(22,39,56,20),f(const Color(0xFFE3C27A)));for(final p in <Offset>[Offset(31,49),Offset(40,45),Offset(50,52),Offset(61,46),Offset(69,51)])c.drawCircle(p,2.1,f(const Color(0xFFB07A3E)));c.drawCircle(const Offset(48,46),5,f(const Color(0xFF7C4A31)));break;case 'jerusalem_kaak':final p=Path()..addOval(const Rect.fromLTWH(21,30,58,48));c.drawPath(p,f(const Color(0xFFD99D4B)));c.drawOval(const Rect.fromLTWH(36,41,28,26),f(const Color(0xFFF6E6C5)));for(final q in <Offset>[Offset(31,41),Offset(42,34),Offset(56,34),Offset(69,43),Offset(70,58),Offset(58,70),Offset(42,70),Offset(29,58)])c.drawCircle(q,1.5,f(const Color(0xFFF1E0B2)));break;}c.restore();}
  @override bool shouldRepaint(covariant FoodPictogramPainterBatch33 o)=>o.foodId!=foodId;
}
