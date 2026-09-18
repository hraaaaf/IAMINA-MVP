import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch23Ids=<String>{'yemeni_saltah','yemeni_fahsa','yemeni_bint_al_sahn'};
bool hasCodeFoodPictogramBatch23(String foodId)=>codeFoodPictogramBatch23Ids.contains(foodId);
class FoodPictogramPainterBatch23 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch23(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,78,60,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'yemeni_saltah':c.drawOval(const Rect.fromLTWH(19,43,62,34),f(const Color(0xFF704B37)));c.drawOval(const Rect.fromLTWH(25,47,50,22),f(const Color(0xFFB98B52)));for(final x in <double>[34,46,58,68])c.drawCircle(Offset(x,51+(x%3)),3.5,f(const Color(0xFF7FA05C)));c.drawArc(const Rect.fromLTWH(29,49,42,16),0,math.pi,false,s(const Color(0xFFE7E0B4),3));break;case 'yemeni_fahsa':c.drawOval(const Rect.fromLTWH(20,44,60,33),f(const Color(0xFF6E4938)));c.drawOval(const Rect.fromLTWH(26,48,48,20),f(const Color(0xFF9A5A3C)));for(final r in <Rect>[Rect.fromLTWH(32,50,10,7),Rect.fromLTWH(46,56,11,7),Rect.fromLTWH(59,49,9,8)])c.drawRRect(RRect.fromRectAndRadius(r,const Radius.circular(3)),f(const Color(0xFF6B3F2C)));c.drawArc(const Rect.fromLTWH(31,47,38,17),0,math.pi,false,s(const Color(0xFF9FB46D),3));break;case 'yemeni_bint_al_sahn':for(var i=0;i<4;i++){final y=38.0+i*8;c.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(24.0+i, y,52.0-i*2,10),const Radius.circular(4)),f(Color.lerp(const Color(0xFFE5B45D),const Color(0xFFC88435),i/4)!));}c.drawPath(Path()..moveTo(31,38)..quadraticBezierTo(50,30,69,38),s(const Color(0xFFF2C94C),4));for(final x in <double>[37,50,63])c.drawCircle(Offset(x,43),2,f(const Color(0xFF2F2A25)));break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch23 o)=>o.foodId!=foodId;
}
