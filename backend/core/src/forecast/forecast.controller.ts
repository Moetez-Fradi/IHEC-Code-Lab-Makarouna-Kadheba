import {
  Controller,
  Get,
  Query,
  UseGuards,
  BadRequestException,
  InternalServerErrorException,
} from '@nestjs/common';
import { ForecastService } from './forecast.service.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';

@Controller('forecast')
export class ForecastController {
  constructor(private readonly forecastService: ForecastService) {}

  /**
   * GET /api/forecast?code=XXX&lookback=500
   *
   * Returns 5-day price/volume/liquidity forecast for a stock.
   * Protected – requires a valid JWT bearer token.
   */
  @UseGuards(JwtAuthGuard)
  @Get()
  async getForecast(
    @Query('code') code: string,
    @Query('lookback') lookback?: string,
  ) {
    if (!code)
      throw new BadRequestException("'code' query parameter is required");

    try {
      return await this.forecastService.getForecast(
        code,
        lookback ? parseInt(lookback, 10) : undefined,
      );
    } catch (err) {
      throw new InternalServerErrorException(
        `Forecasting failed: ${(err as Error).message}`,
      );
    }
  }
}
