import 'package:dio/dio.dart';

import '../../core/errors/app_exception.dart';
import '../../core/network/dio_client.dart';
import '../models/crypto_asset_model.dart';

class MarketRemoteDataSource {
  final DioClient client;

  const MarketRemoteDataSource(this.client);

  Future<List<CryptoAssetModel>> fetchTopMarkets() async {
    try {
      final response = await client.dio.get(
        '/coins/markets',
        queryParameters: {
          'vs_currency': 'usd',
          'order': 'market_cap_desc',
          'per_page': 50,
          'page': 1,
          'sparkline': false,
          'price_change_percentage': '24h',
        },
      );

      final data = response.data as List<dynamic>;

      return data
          .map(
            (item) => CryptoAssetModel.fromJson(item as Map<String, dynamic>),
          )
          .toList();
    } on DioException catch (e) {
      throw AppException(
        e.response?.data.toString() ?? 'Market data request failed',
        statusCode: e.response?.statusCode,
      );
    } catch (_) {
      throw const AppException('Unexpected market data error');
    }
  }
}
