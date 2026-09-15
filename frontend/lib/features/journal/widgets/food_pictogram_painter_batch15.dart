import 'dart:math' as math;

import 'package:flutter/material.dart';

const Set<String> codeFoodPictogramBatch15Ids = <String>{
  'matazeez','areeka','masoub','haneeth','maghsh','samak_mkashan','mahshoosh','marsah','gahwa_gishr','tasabea','mashgotha','miva_bread','qabooli','mishkak','omani_halwa','lamb_khuzi','bahraini_halwa','malgoum','louba_bahraini','bahraini_tikka','tashreeb','murabiyan','mutabbaq_zubaidi','dakkous',
};

bool hasCodeFoodPictogramBatch15(String foodId) => codeFoodPictogramBatch15Ids.contains(foodId);

class FoodPictogramPainterBatch15 extends CustomPainter {
  final String foodId;
  const FoodPictogramPainterBatch15(this.foodId);

  Paint _fill(Color c) => Paint()..color = c..isAntiAlias = true;
  Paint _stroke(Color c, double w) => Paint()..color = c..style = PaintingStyle.stroke..strokeWidth = w..strokeCap = StrokeCap.round..strokeJoin = StrokeJoin.round..isAntiAlias = true;
  void _shadow(Canvas c) => c.drawShadow(Path()..addOval(const Rect.fromLTWH(20,76,60,7)), Colors.black.withValues(alpha:.14), 4, false);
  void _plate(Canvas c){_shadow(c); c.drawOval(const Rect.fromLTWH(18,50,64,29),_fill(const Color(0xFFF7FAF9)));}

  @override
  void paint(Canvas canvas, Size size) {
    final side=math.min(size.width,size.height);
    canvas.save(); canvas.translate((size.width-side)/2,(size.height-side)/2); canvas.scale(side/100,side/100);
    switch(foodId){
      case 'qabooli': _rice(canvas,const Color(0xFFD3A754),nuts:true); break;
      case 'murabiyan': _rice(canvas,const Color(0xFFE0B966),shrimp:true); break;
      case 'lamb_khuzi': _rice(canvas,const Color(0xFFD2A456),lamb:true); break;
      case 'mutabbaq_zubaidi': _rice(canvas,const Color(0xFFE2C071),fish:true); break;
      case 'matazeez': _stew(canvas,const Color(0xFFA96342),dough:true); break;
      case 'maghsh': _stew(canvas,const Color(0xFF8E5A3F),meat:true); break;
      case 'tashreeb': _stew(canvas,const Color(0xFFB55C3F),bread:true); break;
      case 'haneeth': _roast(canvas,const Color(0xFF9C5E3F)); break;
      case 'mahshoosh': _roast(canvas,const Color(0xFF7D4A36),chopped:true); break;
      case 'samak_mkashan': _fish(canvas,const Color(0xFFB97A42)); break;
      case 'mishkak': _skewer(canvas,const Color(0xFFA65E3E)); break;
      case 'bahraini_tikka': _skewer(canvas,const Color(0xFF8F4D39),lime:true); break;
      case 'areeka': _porridge(canvas,const Color(0xFFB88B4D),dates:true); break;
      case 'masoub': _porridge(canvas,const Color(0xFFC59A58),banana:true); break;
      case 'marsah': _porridge(canvas,const Color(0xFFD1A25B),honey:true); break;
      case 'tasabea': _porridge(canvas,const Color(0xFFE1D1A1),ghee:true); break;
      case 'mashgotha': _porridge(canvas,const Color(0xFFD6C393),honey:true); break;
      case 'louba_bahraini': _beans(canvas); break;
      case 'miva_bread': _bread(canvas); break;
      case 'gahwa_gishr': _coffee(canvas); break;
      case 'omani_halwa': _halwa(canvas,const Color(0xFF8F4D38)); break;
      case 'bahraini_halwa': _halwa(canvas,const Color(0xFFB54235)); break;
      case 'malgoum': _wrap(canvas); break;
      case 'dakkous': _sauce(canvas); break;
    }
    canvas.restore();
  }

  void _rice(Canvas c,Color rice,{bool nuts=false,bool shrimp=false,bool lamb=false,bool fish=false}){_plate(c);c.drawOval(const Rect.fromLTWH(25,43,50,26),_fill(rice));if(nuts)for(final p in const [Offset(40,50),Offset(53,46),Offset(62,53)])c.drawOval(Rect.fromCenter(center:p,width:6,height:3),_fill(const Color(0xFF8C633E)));if(shrimp)c.drawArc(const Rect.fromLTWH(40,43,23,16),-.4,4.6,false,_stroke(const Color(0xFFE97854),5));if(lamb)c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(39,42,25,12),const Radius.circular(5)),_fill(const Color(0xFF8B513A)));if(fish){c.drawOval(const Rect.fromLTWH(35,42,31,13),_fill(const Color(0xFFB98F69)));c.drawPath(Path()..moveTo(65,48)..lineTo(74,42)..lineTo(73,55)..close(),_fill(const Color(0xFFB98F69)));}}
  void _stew(Canvas c,Color broth,{bool dough=false,bool meat=false,bool bread=false}){_shadow(c);c.drawOval(const Rect.fromLTWH(18,45,64,34),_fill(const Color(0xFFE7EFEC)));c.drawOval(const Rect.fromLTWH(24,37,52,26),_fill(broth));if(dough)for(final p in const [Offset(39,47),Offset(52,44),Offset(63,50)])c.drawCircle(p,4,_fill(const Color(0xFFE5C58A)));if(meat)for(final p in const [Offset(41,46),Offset(58,49)])c.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center:p,width:12,height:8),const Radius.circular(3)),_fill(const Color(0xFF754633)));if(bread)for(final p in const [Offset(39,48),Offset(53,44),Offset(64,51)])c.drawRect(Rect.fromCenter(center:p,width:11,height:7),_fill(const Color(0xFFD9B774)));}
  void _roast(Canvas c,Color meat,{bool chopped=false}){_plate(c);if(chopped){for(final p in const [Offset(38,50),Offset(51,47),Offset(62,54),Offset(48,59)])c.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center:p,width:14,height:9),const Radius.circular(3)),_fill(meat));}else{c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(31,39,40,25),const Radius.circular(11)),_fill(meat));c.drawLine(const Offset(62,43),const Offset(76,34),_stroke(const Color(0xFFE7D5B2),5));}}
  void _fish(Canvas c,Color body){_plate(c);c.drawOval(const Rect.fromLTWH(29,41,42,20),_fill(body));c.drawPath(Path()..moveTo(68,51)..lineTo(80,40)..lineTo(79,62)..close(),_fill(body));c.drawCircle(const Offset(38,48),1.8,_fill(const Color(0xFF253A38)));for(double x=46;x<65;x+=7)c.drawLine(Offset(x,45),Offset(x-2,57),_stroke(const Color(0xFFF3D5A4),1.5));}
  void _skewer(Canvas c,Color meat,{bool lime=false}){_plate(c);c.drawLine(const Offset(27,66),const Offset(72,35),_stroke(const Color(0xFF9A7248),2));for(final p in const [Offset(38,58),Offset(48,51),Offset(58,44)])c.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center:p,width:14,height:10),const Radius.circular(3)),_fill(meat));if(lime)c.drawCircle(const Offset(66,61),6,_fill(const Color(0xFF9CB84F)));}
  void _porridge(Canvas c,Color base,{bool dates=false,bool banana=false,bool honey=false,bool ghee=false}){_shadow(c);c.drawOval(const Rect.fromLTWH(20,45,60,32),_fill(const Color(0xFFE5ECEA)));c.drawOval(const Rect.fromLTWH(26,39,48,23),_fill(base));if(dates)for(final p in const [Offset(40,48),Offset(60,48)])c.drawOval(Rect.fromCenter(center:p,width:9,height:5),_fill(const Color(0xFF744630)));if(banana)for(final p in const [Offset(40,48),Offset(51,44),Offset(61,50)])c.drawCircle(p,4,_fill(const Color(0xFFEBD27B)));if(honey)c.drawArc(const Rect.fromLTWH(37,42,27,13),0,math.pi*1.8,false,_stroke(const Color(0xFFD8922E),2.5));if(ghee)c.drawCircle(const Offset(51,48),5,_fill(const Color(0xFFF0C85B)));}
  void _beans(Canvas c){_stew(c,const Color(0xFFA65F42));for(final p in const [Offset(38,47),Offset(49,52),Offset(60,46)])c.drawOval(Rect.fromCenter(center:p,width:8,height:5),_fill(const Color(0xFF6E8D49)));}
  void _bread(Canvas c){_plate(c);final p=Path()..moveTo(29,57)..quadraticBezierTo(32,34,51,34)..quadraticBezierTo(71,35,73,57)..quadraticBezierTo(52,69,29,57)..close();c.drawPath(p,_fill(const Color(0xFFD6A45E)));for(final x in const [42.0,52.0,62.0])c.drawLine(Offset(x,41),Offset(x-5,54),_stroke(const Color(0xFFF0CE91),2));}
  void _coffee(Canvas c){c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(31,40,35,29),const Radius.circular(8)),_fill(const Color(0xFFF4EFE4)));c.drawOval(const Rect.fromLTWH(34,42,29,11),_fill(const Color(0xFF7A4E35)));c.drawArc(const Rect.fromLTWH(60,47,19,17),-1.2,2.4,false,_stroke(const Color(0xFFF4EFE4),5));c.drawPath(Path()..moveTo(40,34)..quadraticBezierTo(44,27,48,34),_stroke(const Color(0xFF9FB5AE),1.5));c.drawPath(Path()..moveTo(52,34)..quadraticBezierTo(56,27,60,34),_stroke(const Color(0xFF9FB5AE),1.5));}
  void _halwa(Canvas c,Color color){_plate(c);c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(31,39,39,26),const Radius.circular(8)),_fill(color));for(final p in const [Offset(41,47),Offset(55,44),Offset(61,55),Offset(46,57)])c.drawOval(Rect.fromCenter(center:p,width:6,height:3),_fill(const Color(0xFFDDBD74)));}
  void _wrap(Canvas c){_plate(c);final p=Path()..moveTo(34,35)..quadraticBezierTo(51,31,68,39)..lineTo(60,70)..lineTo(42,70)..close();c.drawPath(p,_fill(const Color(0xFFE0C58A)));c.drawCircle(const Offset(44,44),4,_fill(const Color(0xFF80A762)));c.drawCircle(const Offset(54,43),4,_fill(const Color(0xFF9A5A3E)));c.drawCircle(const Offset(62,47),4,_fill(const Color(0xFFC95B43)));}
  void _sauce(Canvas c){_shadow(c);c.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(29,42,42,31),const Radius.circular(11)),_fill(const Color(0xFFF5F0E7)));c.drawOval(const Rect.fromLTWH(33,44,34,18),_fill(const Color(0xFFC84D3B)));c.drawOval(const Rect.fromLTWH(48,38,7,5),_fill(const Color(0xFF6D9858)));}

  @override
  bool shouldRepaint(covariant FoodPictogramPainterBatch15 oldDelegate)=>oldDelegate.foodId!=foodId;
}
