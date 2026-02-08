import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class ForecastService {
  private readonly logger = new Logger(ForecastService.name);
  private readonly baseUrl: string;

  constructor(private readonly configService: ConfigService) {
    this.baseUrl =
      this.configService.get<string>('FORECAST_SERVICE_URL') ??
      'http://localhost:8002';
  }

  /**
   * Forward the forecast request to the Python forecasting micro-service
   * and return the JSON report as-is.
   */
  async getForecast(code: string, lookback?: number): Promise<any> {
    const params = new URLSearchParams({ code });
    if (lookback) params.append('lookback', String(lookback));

    const url = `${this.baseUrl}/forecast?${params.toString()}`;
    this.logger.log(`Calling forecast service: ${url}`);

    const res = await fetch(url);

    if (!res.ok) {
      const body = await res.text();
      this.logger.error(`Forecast service error ${res.status}: ${body}`);
      throw new Error(`Forecast service returned ${res.status}: ${body}`);
    }

    return res.json();
  }
}
