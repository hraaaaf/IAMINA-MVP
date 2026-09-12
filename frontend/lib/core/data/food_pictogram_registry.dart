/// Registry of premium food pictograms that are physically present in the
/// Flutter bundle and have passed the IAMINA visual review.
///
/// Keep this set empty until the corresponding WebP is committed. Adding an ID
/// here is an explicit certification step, not a declaration of intent.
const Set<String> certifiedFoodPictogramIds = <String>{};

bool hasCertifiedFoodPictogram(String foodId) =>
    certifiedFoodPictogramIds.contains(foodId);

String certifiedFoodPictogramPath(String foodId) =>
    'assets/food/pictograms/v1/$foodId.webp';
