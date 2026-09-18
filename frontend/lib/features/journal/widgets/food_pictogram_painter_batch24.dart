import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch24Ids=<String>{'moroccan_amlou','moroccan_khlii','moroccan_taktouka'};
bool hasCodeFoodPictogramBatch24(String foodId)=>codeFoodPictogramBatch24Ids.contains(foodId);
class FoodPictogramPainterBatch24 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch24(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,78,60,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'moroccan_amlou':c.drawOval(const Rect.fromLTWH(20,48,60,28),f(const Color(0xFF8B5A36)));c.drawOval(const Rect.fromLTWH(26,50,48,18),f(const Color(0xFFC58A4A)));for(final x in <double>[34,47,61,69])c.drawOval(Rect.fromCenter(center:Offset(x,48+(x%4)),width:8,height:5),f(const Color(0xFFE2B56F)));c.drawPath(Path()..moveTo(32,58)..quadraticBezierTo(50,51,68,58),s(const Color(0xFFF1C453),3));break;case 'moroccan_khlii':c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(20,48,60,28),const Radius.circular(10)),f(const Color(0xFF6C3F2C)));for(final r in <Rect>[Rect.fromLTWH(27,52,14,8),Rect.fromLTWH(44,58,15,8),Rect.fromLTWH(61,51,11,9)])c.drawRRect(RRect.fromRectAndRadius(r,const Radius.circular(3)),f(const Color(0xFF9B6040)));c.drawArc(const Rect.fromLTWH(25,46,50,23),0,math.pi,false,s(const Color(0xFFD8A15B),3));break;case 'moroccan_taktouka':c.drawOval(const Rect.fromLTWH(19,48,62,28),f(const Color(0xFFB84A3A)));c.drawOval(const Rect.fromLTWH(25,51,50,18),f(const Color(0xFFD95D45)));for(final x in <double>[33,45,57,68]){c.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(x-4,53+(x%3),8,6),const Radius.circular(3)),f(const Color(0xFF4F8A4B)));}c.drawCircle(const Offset(50,58),3,f(const Color(0xFFF2B544)));break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch24 o)=>o.foodId!=foodId;
}
