import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch18Ids=<String>{'tagoula','ourkimen','tehal_stuffed_spleen'};
bool hasCodeFoodPictogramBatch18(String foodId)=>codeFoodPictogramBatch18Ids.contains(foodId);

class FoodPictogramPainterBatch18 extends CustomPainter{
  final String foodId; const FoodPictogramPainterBatch18(this.foodId);
  Paint _fill(Color c)=>Paint()..color=c..isAntiAlias=true;
  Paint _stroke(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..strokeJoin=StrokeJoin.round..isAntiAlias=true;
  void _shadow(Canvas c)=>c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,76,60,7)),Colors.black.withValues(alpha:.14),4,false);
  @override void paint(Canvas canvas,Size size){final side=math.min(size.width,size.height);canvas.save();canvas.translate((size.width-side)/2,(size.height-side)/2);canvas.scale(side/100,side/100);switch(foodId){case 'tagoula':_tagoula(canvas);break;case 'ourkimen':_ourkimen(canvas);break;case 'tehal_stuffed_spleen':_tehal(canvas);break;}canvas.restore();}
  void _tagoula(Canvas c){_shadow(c);c.drawOval(const Rect.fromLTWH(20,43,60,33),_fill(const Color(0xFF7FA39A)));c.drawOval(const Rect.fromLTWH(25,38,50,28),_fill(const Color(0xFFD8B46A)));c.drawArc(const Rect.fromLTWH(29,42,42,18),.2,math.pi-.4,false,_stroke(const Color(0xFFB38A46),1.5));c.drawCircle(const Offset(50,49),4,_fill(const Color(0xFF8A5B36)));c.drawCircle(const Offset(61,46),2.5,_fill(const Color(0xFF7B4A2D)));}
  void _ourkimen(Canvas c){_shadow(c);c.drawOval(const Rect.fromLTWH(20,42,60,34),_fill(const Color(0xFF6F9B91)));c.drawOval(const Rect.fromLTWH(25,37,50,29),_fill(const Color(0xFF9B6A3C)));for(final p in <Offset>[Offset(37,47),Offset(48,52),Offset(59,46),Offset(64,55),Offset(42,58)]){c.drawCircle(p,3,_fill(const Color(0xFFD7B36B)));}c.drawArc(const Rect.fromLTWH(29,41,42,18),.15,math.pi-.3,false,_stroke(const Color(0xFF74482C),1.5));}
  void _tehal(Canvas c){_shadow(c);final body=Path()..moveTo(27,49)..quadraticBezierTo(38,34,61,38)..quadraticBezierTo(76,41,74,55)..quadraticBezierTo(71,69,50,71)..quadraticBezierTo(29,70,25,59)..close();c.drawPath(body,_fill(const Color(0xFF7A3F38)));c.drawPath(body,_stroke(const Color(0xFF552B28),2));c.drawLine(const Offset(35,48),const Offset(66,58),_stroke(const Color(0xFFD6B48C),2));for(final x in <double>[41,52,62]){c.drawCircle(Offset(x,53+(x-50)*.18),2,_fill(const Color(0xFFE0C49E)));}}
  @override bool shouldRepaint(covariant FoodPictogramPainterBatch18 oldDelegate)=>oldDelegate.foodId!=foodId;
}
