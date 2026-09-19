import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch26Ids=<String>{'libyan_bazin','libyan_mbakbaka','libyan_shorba'};
bool hasCodeFoodPictogramBatch26(String foodId)=>codeFoodPictogramBatch26Ids.contains(foodId);
class FoodPictogramPainterBatch26 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch26(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,78,60,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'libyan_bazin':c.drawOval(const Rect.fromLTWH(18,48,64,29),f(const Color(0xFF9A593A)));c.drawOval(const Rect.fromLTWH(24,51,52,19),f(const Color(0xFFC94F35)));c.drawOval(const Rect.fromLTWH(38,43,24,24),f(const Color(0xFFC9A36A)));c.drawCircle(const Offset(31,58),5,f(const Color(0xFFF1D36A)));c.drawCircle(const Offset(69,59),5,f(const Color(0xFFF1D36A)));break;case 'libyan_mbakbaka':c.drawOval(const Rect.fromLTWH(19,48,62,28),f(const Color(0xFF7E4B35)));c.drawOval(const Rect.fromLTWH(25,50,50,20),f(const Color(0xFFC84D32)));for(final r in <Rect>[Rect.fromLTWH(30,54,13,5),Rect.fromLTWH(45,60,14,5),Rect.fromLTWH(59,53,12,5)])c.drawRRect(RRect.fromRectAndRadius(r,const Radius.circular(2)),f(const Color(0xFFE8B35C)));c.drawCircle(const Offset(52,54),2.5,f(const Color(0xFF6F8D45)));break;case 'libyan_shorba':c.drawOval(const Rect.fromLTWH(19,48,62,28),f(const Color(0xFF8C5738)));c.drawOval(const Rect.fromLTWH(25,50,50,19),f(const Color(0xFFC94B32)));for(final p in <Offset>[Offset(35,57),Offset(45,62),Offset(56,56),Offset(66,61)])c.drawCircle(p,2.3,f(const Color(0xFFD9B26A)));c.drawPath(Path()..moveTo(40,53)..quadraticBezierTo(50,46,60,53),s(const Color(0xFF6F8D45),2.5));break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch26 o)=>o.foodId!=foodId;
}
