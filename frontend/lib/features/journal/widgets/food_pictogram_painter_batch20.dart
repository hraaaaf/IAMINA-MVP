import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch20Ids=<String>{'omani_shuwa','omani_qabooli','omani_mishkak'};
bool hasCodeFoodPictogramBatch20(String foodId)=>codeFoodPictogramBatch20Ids.contains(foodId);
class FoodPictogramPainterBatch20 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch20(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,78,60,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'omani_shuwa':c.drawOval(const Rect.fromLTWH(21,55,58,22),f(const Color(0xFFD6B36A)));c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(31,37,38,29),const Radius.circular(12)),f(const Color(0xFF7B4632)));c.drawLine(const Offset(38,45),const Offset(60,58),s(const Color(0xFFD8A06A),3));break;case 'omani_qabooli':c.drawOval(const Rect.fromLTWH(20,47,60,30),f(const Color(0xFF4F8178)));c.drawOval(const Rect.fromLTWH(25,40,50,27),f(const Color(0xFFE5C77D)));for(final p in <Offset>[Offset(36,51),Offset(47,46),Offset(58,54),Offset(66,47)])c.drawCircle(p,3,f(const Color(0xFF8A5134)));break;case 'omani_mishkak':for(final y in <double>[39,51,63]){c.drawLine(Offset(27,y+8),Offset(73,y-8),s(const Color(0xFFC69B62),3));for(final x in <double>[37,49,61])c.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center:Offset(x,y+(50-x)*.35),width:10,height:8),const Radius.circular(3)),f(const Color(0xFF9A4E32)));}break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch20 o)=>o.foodId!=foodId;
}
