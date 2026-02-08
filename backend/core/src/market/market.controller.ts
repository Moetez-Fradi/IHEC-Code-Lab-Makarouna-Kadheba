import {
  Controller,
  Get,
  Param,
  Query,
  UseGuards,
} from '@nestjs/common';
import { MarketService } from './market.service.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';

@Controller('market')
export class MarketController {
  constructor(private readonly marketService: MarketService) {}

  /** GET /market/stocks — list all stock codes & names */
  @UseGuards(JwtAuthGuard)
  @Get('stocks')
  getStocks() {
    return this.marketService.getStocks();
  }

  /** GET /market/overview — latest session with % change */
  @UseGuards(JwtAuthGuard)
  @Get('overview')
  getOverview() {
    return this.marketService.getMarketOverview();
  }

  /** GET /market/latest — latest session raw data */
  @UseGuards(JwtAuthGuard)
  @Get('latest')
  getLatest() {
    return this.marketService.getLatestSession();
  }

  /** GET /market/history/:code?days=90 — historical data for a stock */
  @UseGuards(JwtAuthGuard)
  @Get('history/:code')
  getHistory(
    @Param('code') code: string,
    @Query('days') days?: string,
  ) {
    return this.marketService.getStockLatest(code, days ? parseInt(days, 10) : 90);
  }

  /** GET /market/dates — all session dates */
  @UseGuards(JwtAuthGuard)
  @Get('dates')
  getDates() {
    return this.marketService.getSessionDates();
  }
}
