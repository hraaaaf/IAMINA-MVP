import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch22Ids=<String>{'algerian_rechta','algerian_chakhchoukha','algerian_mhadjeb'};
bool hasCodeFoodPictogramBatch22(String foodId)=>codeFoodPictogramBatch22Ids.contains(foodId);
class FoodPictogramPainterBatch22 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch22(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,78,60,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'algerian_rechta':c.drawOval(const Rect.fromLTWH(20,43,60,33),f(const Color(0xFFE6DED0)));for(final y in <double>[51,57,63])c.drawArc(Rect.fromLTWH(29,y,42,8),0,math.pi,false,s(const Color(0xFFE5C87A),3));c.drawCircle(const Offset(38,49),4,f(const Color(0xFFD9B56C)));c.drawCircle(const Offset(62,50),4,f(const Color(0xFFB8C46A)));break;case 'algerian_chakhchoukha':c.drawOval(const Rect.fromLTWH(20,43,60,34),f(const Color(0xFFB65C3D)));for(final r in <Rect>[Rect.fromLTWH(29,49,12,9),Rect.fromLTWH(44,58,13,8),Rect.fromLTWH(59,50,11,9)])c.drawRRect(RRect.fromRectAndRadius(r,const Radius.circular(2)),f(const Color(0xFFE2C184)));c.drawCircle(const Offset(51,49),4,f(const Color(0xFFD7B55E)));break;case 'algerian_mhadjeb':final p=Path()..moveTo(24,68)..lineTo(36,35)..lineTo(76,43)..lineTo(65,72)..close();c.drawPath(p,f(const Color(0xFFD89A4A)));c.drawPath(Path()..moveTo(33,62)..lineTo(42,45)..lineTo(67,49)..lineTo(61,65)..close(),f(const Color(0xFFB84E35)));c.drawLine(const Offset(28,67),const Offset(68,71),s(const Color(0xFFA86E35),2));break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch22 o)=>o.foodId!=foodId;
}
