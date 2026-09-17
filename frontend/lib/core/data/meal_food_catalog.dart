import 'dart:convert';

import 'meal_food_catalog_v3.dart' as base;
import 'meal_food_gulf_core.dart';
import 'meal_food_morocco_regional_b16.dart';
import 'meal_food_morocco_depth_b17.dart';
import 'meal_food_morocco_amazigh_b18.dart';
import 'meal_food_qatar_depth_b19.dart';
import 'meal_food_oman_depth_b20.dart';
import 'meal_food_tunisia_depth_b21.dart';
import 'meal_food_algeria_depth_b22.dart';

export 'meal_food_catalog_v3.dart'
    hide
        mealFoodCatalogVersion,
        mealFoodCatalog,
        mealFoodById,
        mealFoodsForRegion,
        mealFoodsForCategory,
        mealFoodsForMoment,
        decodeMealItemIds,
        encodeMealItemIds,
        searchMealFoods,
        matchRecognizedMealFoods;

/// Catalog facade preserving the certified 322-item V3 baseline byte-for-byte
/// while allowing reviewed regional extensions to remain modular.
const String mealFoodCatalogVersion = '3.8.0-algeria-depth-b22';

const List<base.MealFoodItem> mealFoodCatalog = <base.MealFoodItem>[
  ...base.mealFoodCatalog,
  ...gulfCoreFoodCatalog,
  ...moroccoRegionalB16FoodCatalog,
  ...moroccoDepthB17FoodCatalog,
  ...moroccoAmazighB18FoodCatalog,
  ...qatarDepthB19FoodCatalog,
  ...omanDepthB20FoodCatalog,
  ...tunisiaDepthB21FoodCatalog,
  ...algeriaDepthB22FoodCatalog,
];

final Map<String, base.MealFoodItem> _mealFoodById = <String, base.MealFoodItem>{for (final item in mealFoodCatalog) item.id: item};
base.MealFoodItem? mealFoodById(String id) => _mealFoodById[id];
List<base.MealFoodItem> mealFoodsForRegion(base.MealFoodRegion region) => mealFoodCatalog.where((item) => item.regions.contains(region)).toList(growable: false);
List<base.MealFoodItem> mealFoodsForCategory(base.MealFoodCategory category) => mealFoodCatalog.where((item) => item.category == category).toList(growable: false);
List<base.MealFoodItem> mealFoodsForMoment(base.MealFoodMoment moment) => mealFoodCatalog.where((item) => item.moments.contains(moment)).toList(growable: false);
List<String> decodeMealItemIds(String? raw) {if(raw==null||raw.trim().isEmpty)return const <String>[];try{final decoded=jsonDecode(raw);if(decoded is! List)return const <String>[];return decoded.whereType<String>().where(_mealFoodById.containsKey).toList(growable:false);}catch(_){return const <String>[];}}
String encodeMealItemIds(Iterable<String> ids)=>jsonEncode(ids.where(_mealFoodById.containsKey).toSet().toList(growable:false));
int _mealSearchScore(base.MealFoodItem item,String folded){final values=<String>[item.fr,item.en,item.ar,...item.aliases].map(base.foldMealText).where((value)=>value.isNotEmpty).toList(growable:false);if(values.any((value)=>value==folded))return 100;if(values.any((value)=>value.startsWith(folded)))return 80;if(values.any((value)=>value.contains(folded)))return 60;final terms=folded.split(' ').where((term)=>term.isNotEmpty).toList();if(terms.isNotEmpty&&terms.every((term)=>base.foldMealText(item.searchable).contains(term)))return 40;return 0;}
List<base.MealFoodItem> searchMealFoods(String query,{int limit=12}){final folded=base.foldMealText(query);if(folded.length<2)return const <base.MealFoodItem>[];final scored=<MapEntry<base.MealFoodItem,int>>[];for(final item in mealFoodCatalog){final score=_mealSearchScore(item,folded);if(score>0)scored.add(MapEntry(item,score));}scored.sort((a,b){final byScore=b.value.compareTo(a.value);if(byScore!=0)return byScore;return a.key.fr.compareTo(b.key.fr);});return scored.take(limit).map((entry)=>entry.key).toList(growable:false);}
List<base.MealFoodItem> matchRecognizedMealFoods(Iterable<String> recognized){final found=<String,base.MealFoodItem>{};for(final raw in recognized){final needle=base.foldMealText(raw);if(needle.isEmpty)continue;final ranked=searchMealFoods(raw,limit:1);if(ranked.isNotEmpty)found[ranked.first.id]=ranked.first;}return found.values.take(8).toList(growable:false);}
