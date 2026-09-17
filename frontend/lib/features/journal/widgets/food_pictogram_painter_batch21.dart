import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch21Ids=<String>{'tunisian_brik','tunisian_lablabi','tunisian_kafteji'};
bool hasCodeFoodPictogramBatch21(String foodId)=>codeFoodPictogramBatch21Ids.contains(foodId);
class FoodPictogramPainterBatch21 extends CustomPainter{
 final String foodId; const FoodPictogramPainterBatch21(this.foodId);
 Paint f(Color c)=>Paint()..color=c..isAntiAlias=true; Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;
 @override void paint(Canvas c,Size z){final d=math.min(z.width,z.height);c.save();c.translate((z.width-d)/2,(z.height-d)/2);c.scale(d/100,d/100);c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,78,60,6)),Colors.black.withValues(alpha:.14),4,false);switch(foodId){case 'tunisian_brik':final p=Path()..moveTo(22,68)..lineTo(50,28)..lineTo(78,68)..close();c.drawPath(p,f(const Color(0xFFE0A34C)));c.drawCircle(const Offset(50,52),9,f(const Color(0xFFF4D24D)));c.drawCircle(const Offset(50,52),4,f(const Color(0xFFE7A51E)));break;case 'tunisian_lablabi':c.drawOval(const Rect.fromLTWH(20,42,60,34),f(const Color(0xFFE7E0D2)));c.drawOval(const Rect.fromLTWH(25,46,50,24),f(const Color(0xFFD69A48)));for(final x in <double>[34,45,56,66])c.drawCircle(Offset(x,57+(x%3)),4,f(const Color(0xFFF0C76E)));c.drawLine(const Offset(31,48),const Offset(68,68),s(const Color(0xFFB94B35),2));break;case 'tunisian_kafteji':c.drawOval(const Rect.fromLTWH(21,45,58,30),f(const Color(0xFF5E5145)));for(final r in <Rect>[Rect.fromLTWH(29,51,13,9),Rect.fromLTWH(44,58,14,9),Rect.fromLTWH(59,50,11,9)])c.drawRRect(RRect.fromRectAndRadius(r,const Radius.circular(3)),f(const Color(0xFFB95C38)));c.drawCircle(const Offset(48,52),8,f(const Color(0xFFF4D45B)));break;}c.restore();}
 @override bool shouldRepaint(covariant FoodPictogramPainterBatch21 o)=>o.foodId!=foodId;
}
