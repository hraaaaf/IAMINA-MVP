import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch31Ids=<String>{'egyptian_koshary','egyptian_ful_medames','egyptian_molokhiya'};
bool hasCodeFoodPictogramBatch31(String foodId)=>codeFoodPictogramBatch31Ids.contains(foodId);

class FoodPictogramPainterBatch31 extends CustomPainter{
  final String foodId;
  const FoodPictogramPainterBatch31(this.foodId);
  Paint f(Color c)=>Paint()..color=c..isAntiAlias=true;
  Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
  @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(18,78,64,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'egyptian_koshary':c.drawOval(const Rect.fromLTWH(18,42,64,34),f(const Color(0xFFB96B3A)));c.drawOval(const Rect.fromLTWH(23,36,54,31),f(const Color(0xFFF3D6A4)));for(final x in <double>[31,41,51,61]) c.drawCircle(Offset(x,48+(x%3)),3.2,f(const Color(0xFF6B4D2E)));for(final x in <double>[34,46,58,68]) c.drawArc(Rect.fromLTWH(x-5,42,10,18),0,math.pi*1.5,false,s(const Color(0xFFC88A42),2));c.drawRect(const Rect.fromLTWH(28,57,44,5),f(const Color(0xFFC94B36)));break;case 'egyptian_ful_medames':c.drawOval(const Rect.fromLTWH(20,45,60,28),f(const Color(0xFF7B4B2E)));c.drawOval(const Rect.fromLTWH(25,41,50,22),f(const Color(0xFF9B6A3D)));for(final p in <Offset>[Offset(35,49),Offset(47,53),Offset(59,48),Offset(66,55)]) c.drawOval(Rect.fromCenter(center:p,width:10,height:6),f(const Color(0xFF5F3F28)));c.drawArc(const Rect.fromLTWH(32,37,36,22),0,math.pi,false,s(const Color(0xFF7E9D4F),3));break;case 'egyptian_molokhiya':c.drawOval(const Rect.fromLTWH(19,47,62,29),f(const Color(0xFF8D5B3C)));c.drawOval(const Rect.fromLTWH(24,42,52,24),f(const Color(0xFF567D3B)));for(final p in <Offset>[Offset(36,50),Offset(48,55),Offset(59,49),Offset(66,57)]) c.drawOval(Rect.fromCenter(center:p,width:9,height:4),f(const Color(0xFF7FA45A)));c.drawLine(const Offset(31,39),const Offset(67,39),s(const Color(0xFFD4B18A),2));break;}c.restore();}
  @override bool shouldRepaint(covariant FoodPictogramPainterBatch31 o)=>o.foodId!=foodId;
}
