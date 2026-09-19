import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch27Ids=<String>{'omani_madrouba','omani_arsia','omani_paplou'};
bool hasCodeFoodPictogramBatch27(String foodId)=>codeFoodPictogramBatch27Ids.contains(foodId);
class FoodPictogramPainterBatch27 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch27(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,78,60,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'omani_madrouba':c.drawOval(const Rect.fromLTWH(18,50,64,28),f(const Color(0xFF9A6745)));c.drawOval(const Rect.fromLTWH(23,48,54,22),f(const Color(0xFFD9B36C)));for(final p in <Offset>[Offset(34,57),Offset(46,61),Offset(59,55),Offset(67,62)])c.drawCircle(p,3,f(const Color(0xFFB97845)));break;case 'omani_arsia':c.drawOval(const Rect.fromLTWH(18,50,64,28),f(const Color(0xFF8A5C42)));c.drawOval(const Rect.fromLTWH(23,48,54,22),f(const Color(0xFFE7D4A0)));c.drawPath(Path()..moveTo(31,59)..quadraticBezierTo(50,48,69,59)..quadraticBezierTo(50,69,31,59),f(const Color(0xFFC7A36A)));break;case 'omani_paplou':c.drawOval(const Rect.fromLTWH(18,50,64,28),f(const Color(0xFF76523E)));c.drawOval(const Rect.fromLTWH(23,48,54,22),f(const Color(0xFFE0A33D)));c.drawOval(const Rect.fromLTWH(36,54,28,10),f(const Color(0xFF5D8C92)));c.drawCircle(const Offset(62,59),2,f(const Color(0xFFEEF2D0)));c.drawLine(const Offset(38,58),const Offset(30,53),s(const Color(0xFF5D8C92),3));break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch27 o)=>o.foodId!=foodId;
}
