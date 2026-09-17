import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch17Ids = <String>{
  'tanjia_marrakchia',
  'chebakia',
  'lben_moroccan',
  'raib_moroccan',
};

bool hasCodeFoodPictogramBatch17(String foodId) => codeFoodPictogramBatch17Ids.contains(foodId);

class FoodPictogramPainterBatch17 extends CustomPainter {
  final String foodId;
  const FoodPictogramPainterBatch17(this.foodId);

  Paint _fill(Color color) => Paint()..color = color..isAntiAlias = true;
  Paint _stroke(Color color, double width) => Paint()..color=color..style=PaintingStyle.stroke..strokeWidth=width..strokeCap=StrokeCap.round..strokeJoin=StrokeJoin.round..isAntiAlias=true;
  void _shadow(Canvas c)=>c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,76,60,7)),Colors.black.withValues(alpha:.14),4,false);

  @override
  void paint(Canvas canvas, Size size) {
    final side=math.min(size.width,size.height);
    canvas.save(); canvas.translate((size.width-side)/2,(size.height-side)/2); canvas.scale(side/100,side/100);
    switch(foodId){
      case 'tanjia_marrakchia': _tanjia(canvas); break;
      case 'chebakia': _chebakia(canvas); break;
      case 'lben_moroccan': _lben(canvas); break;
      case 'raib_moroccan': _raib(canvas); break;
    }
    canvas.restore();
  }

  void _tanjia(Canvas c){
    _shadow(c);
    final jar=Path()..moveTo(37,30)..lineTo(63,30)..lineTo(67,39)..quadraticBezierTo(73,55,66,73)..quadraticBezierTo(50,80,34,73)..quadraticBezierTo(27,55,33,39)..close();
    c.drawPath(jar,_fill(const Color(0xFFC77B45))); c.drawPath(jar,_stroke(const Color(0xFF8B4F31),2.2));
    c.drawRect(const Rect.fromLTWH(39,24,22,8),_fill(const Color(0xFFD9A06D))); c.drawLine(const Offset(42,46),const Offset(58,46),_stroke(const Color(0xFFE5B27E),2));
  }
  void _chebakia(Canvas c){
    _shadow(c); c.drawOval(const Rect.fromLTWH(20,49,60,26),_fill(const Color(0xFFF1F3EF)));
    for(final x in <double>[34,50,66]){final p=Path()..moveTo(x-10,57)..quadraticBezierTo(x,43,x+10,57)..quadraticBezierTo(x,71,x-10,57)..close();c.drawPath(p,_fill(const Color(0xFFB8742E)));c.drawPath(p,_stroke(const Color(0xFF7D4B25),1.6));c.drawLine(Offset(x-5,53),Offset(x+5,62),_stroke(const Color(0xFFE6B85D),1.5));}
  }
  void _lben(Canvas c){
    _shadow(c); final glass=Path()..moveTo(34,31)..lineTo(66,31)..lineTo(62,73)..quadraticBezierTo(50,78,38,73)..close(); c.drawPath(glass,_fill(const Color(0xFFF4F1E7))); c.drawPath(glass,_stroke(const Color(0xFF8FA8A4),2)); c.drawLine(const Offset(36,40),const Offset(64,40),_stroke(const Color(0xFFD8D4C8),1.5));
  }
  void _raib(Canvas c){
    _shadow(c); c.drawOval(const Rect.fromLTWH(22,43,56,32),_fill(const Color(0xFF9BB7B0))); c.drawOval(const Rect.fromLTWH(27,39,46,25),_fill(const Color(0xFFF5F0E6))); c.drawArc(const Rect.fromLTWH(31,43,38,16),.2,math.pi-.4,false,_stroke(const Color(0xFFD8D0C0),1.6)); c.drawCircle(const Offset(57,48),2,_fill(const Color(0xFFE4C38C)));
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch17 oldDelegate)=>oldDelegate.foodId!=foodId;
}
