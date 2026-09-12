import 'dart:convert';
import 'dart:io';

import 'package:amina/core/data/food_pictogram_registry.dart';
import 'package:amina/core/data/meal_food_catalog.dart';

const String _assetDirectory = 'assets/food/pictograms/v1';

Never _fail(String message) {
  stderr.writeln(message);
  exitCode = 1;
  throw StateError(message);
}

void main(List<String> args) {
  final strict = args.contains('--strict');
  final catalogIds = mealFoodCatalog.map((item) => item.id).toSet();
  final registeredIds = certifiedFoodPictogramIds.toSet();

  final unknownRegistered = registeredIds.difference(catalogIds);
  if (unknownRegistered.isNotEmpty) {
    _fail(
      'Certified pictogram registry contains unknown food IDs: '
      '${unknownRegistered.join(', ')}',
    );
  }

  final directory = Directory(_assetDirectory);
  if (!directory.existsSync()) {
    _fail('Missing pictogram asset directory: $_assetDirectory');
  }

  final diskIds = directory
      .listSync(followLinks: false)
      .whereType<File>()
      .where((file) => file.path.toLowerCase().endsWith('.webp'))
      .map((file) {
        final normalized = file.path.replaceAll('\\', '/');
        return normalized.split('/').last.replaceFirst(RegExp(r'\.webp$'), '');
      })
      .toSet();

  final unregisteredFiles = diskIds.difference(registeredIds);
  if (unregisteredFiles.isNotEmpty) {
    _fail(
      'WebP assets exist without certification registry entries: '
      '${unregisteredFiles.join(', ')}',
    );
  }

  final missingFiles = registeredIds.difference(diskIds);
  if (missingFiles.isNotEmpty) {
    _fail(
      'Certified pictograms are missing their WebP files: '
      '${missingFiles.join(', ')}',
    );
  }

  final orphanFiles = diskIds.difference(catalogIds);
  if (orphanFiles.isNotEmpty) {
    _fail(
      'WebP assets do not map to catalog foods: ${orphanFiles.join(', ')}',
    );
  }

  final missingCertification = catalogIds.difference(registeredIds);
  if (strict && missingCertification.isNotEmpty) {
    _fail(
      'Strict pictogram certification incomplete: '
      '${missingCertification.length} catalog foods remain uncertified.',
    );
  }

  final summary = <String, Object>{
    'catalog_version': mealFoodCatalogVersion,
    'catalog_count': catalogIds.length,
    'certified_count': registeredIds.length,
    'asset_count': diskIds.length,
    'remaining_count': missingCertification.length,
    'strict': strict,
    'status': strict ? 'complete' : 'registry_consistent',
  };
  stdout.writeln(const JsonEncoder.withIndent('  ').convert(summary));
}
