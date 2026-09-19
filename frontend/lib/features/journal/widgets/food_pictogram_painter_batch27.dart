import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch27Ids=<String>{'omani_halwa','omani_mishkak','omani_qabooli'};
bool hasCodeFoodPictogramBatch27(String foodId)=>codeFoodPictogramBatch27Ids.contains(foodId);
class FoodPictogramPainterBatch27 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch27(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,78,60,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'omani_halwa':c.drawOval(const Rect.fromLTWH(20,52,60,25),f(const Color(0xFF8A563B)));c.drawOval(const Rect.fromLTWH(25,50,50,20),f(const Color(0xFFB86B45)));for(final p in <Offset>[Offset(36,57),Offset(49,61),Offset(62,56)])c.drawOval(Rect.fromCenter(center:p,width:7,height:4),f(const Color(0xFFE3C67A)));c.drawCircle(const Offset(55,54),2,f(const Color(0xFFD9A83E)));break;case 'omani_mishkak':for(final y in <double>[42,55,68]){c.drawLine(Offset(25,y+8),Offset(76,y-8),s(const Color(0xFFB88B5A),3));for(final x in <double>[36,50,64])c.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center:Offset(x,y+(50-x)*.28),width:11,height:8),const Radius.circular(3)),f(const Color(0xFF8B4933)));}break;case 'omani_qabooli':c.drawOval(const Rect.fromLTWH(18,50,64,27),f(const Color(0xFF8B5A3C)));c.drawOval(const Rect.fromLTWH(23,48,54,21),f(const Color(0xFFE3C56E)));for(final p in <Offset>[Offset(33,56),Offset(43,61),Offset(53,54),Offset(65,59)])c.drawOval(Rect.fromCenter(center:p,width:8,height:4),f(const Color(0xFF7D4A35)));c.drawCircle(const Offset(58,62),2.5,f(const Color(0xFFB66A3C)));break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch27 o)=>o.foodId!=foodId;
}
