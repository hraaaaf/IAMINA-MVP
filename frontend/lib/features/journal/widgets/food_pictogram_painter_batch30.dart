import 'dart:math' as math;
import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch30Ids=<String>{'pizza_margherita','spaghetti_carbonara','lasagne_bolognese'};
bool hasCodeFoodPictogramBatch30(String foodId)=>codeFoodPictogramBatch30Ids.contains(foodId);

class FoodPictogramPainterBatch30 extends CustomPainter{
  final String foodId;
  const FoodPictogramPainterBatch30(this.foodId);
  Paint f(Color c)=>Paint()..color=c..isAntiAlias=true;
  Paint s(Color c,double w)=>Paint()..color=c..style=PaintingStyle.stroke..strokeWidth=w..strokeCap=StrokeCap.round..isAntiAlias=true;

  @override
  void paint(Canvas c,Size z){
    final d=math.min(z.width,z.height);
    c.save();
    c.translate((z.width-d)/2,(z.height-d)/2);
    c.scale(d/100,d/100);
    c.drawShadow(Path()..addOval(const Rect.fromLTWH(18,78,64,6)),Colors.black.withValues(alpha:.14),4,false);
    switch(foodId){
      case 'pizza_margherita':
        c.drawCircle(const Offset(50,52),31,f(const Color(0xFFD39A55)));
        c.drawCircle(const Offset(50,52),25,f(const Color(0xFFC94836)));
        for(final p in <Offset>[Offset(39,43),Offset(57,42),Offset(45,58),Offset(62,57)]) c.drawCircle(p,6,f(const Color(0xFFF7F0D8)));
        for(final p in <Offset>[Offset(50,36),Offset(35,54),Offset(58,64)]) c.drawOval(Rect.fromCenter(center:p,width:8,height:4),f(const Color(0xFF4F8A4C)));
        break;
      case 'spaghetti_carbonara':
        c.drawOval(const Rect.fromLTWH(20,48,60,28),f(const Color(0xFFB36D42)));
        c.drawOval(const Rect.fromLTWH(25,47,50,20),f(const Color(0xFFF3D36A)));
        for(final y in <double>[52,56,60]) c.drawArc(Rect.fromLTWH(31,y-5,38,10),0,math.pi*1.8,false,s(const Color(0xFFE7B94D),2.2));
        for(final p in <Offset>[Offset(39,54),Offset(56,51),Offset(63,59),Offset(47,61)]) c.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center:p,width:6,height:4),const Radius.circular(1.5)),f(const Color(0xFF8B4D32)));
        break;
      case 'lasagne_bolognese':
        c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(24,39,52,35),const Radius.circular(6)),f(const Color(0xFFB55A3C)));
        c.drawRect(const Rect.fromLTWH(28,43,44,6),f(const Color(0xFFF1D07A)));
        c.drawRect(const Rect.fromLTWH(28,51,44,6),f(const Color(0xFFB94733)));
        c.drawRect(const Rect.fromLTWH(28,59,44,6),f(const Color(0xFFF3E0B0)));
        c.drawRect(const Rect.fromLTWH(28,67,44,4),f(const Color(0xFFD39A55)));
        break;
    }
    c.restore();
  }

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch30 o)=>o.foodId!=foodId;
}
