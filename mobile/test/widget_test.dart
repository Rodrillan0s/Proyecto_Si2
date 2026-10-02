import 'package:flutter_test/flutter_test.dart';
import 'package:emergencias_vehiculares/main.dart';

void main() {
  testWidgets('App basic smoke test', (WidgetTester tester) async {
    expect(const ConstructorApp(), isNotNull);
  });
}
