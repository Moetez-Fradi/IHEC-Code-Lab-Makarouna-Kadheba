import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { BvmtData } from './bvmt-data.entity.js';

@Injectable()
export class MarketService {
  constructor(
    @InjectRepository(BvmtData)
    private readonly bvmtRepo: Repository<BvmtData>,
  ) {}

  /** List all distinct stocks (code + valeur) */
  async getStocks(): Promise<{ code: string; valeur: string }[]> {
    const rows = await this.bvmtRepo
      .createQueryBuilder('d')
      .select('d.CODE', 'code')
      .addSelect('d.VALEUR', 'valeur')
      .distinctOn(['"CODE"'])
      .orderBy('"CODE"', 'ASC')
      .getRawMany();
    return rows;
  }

  /** Latest session data for all stocks */
  async getLatestSession() {
    // Find the most recent SEANCE date
    const latest = await this.bvmtRepo
      .createQueryBuilder('d')
      .select('MAX(d.SEANCE)', 'maxDate')
      .getRawOne();

    if (!latest?.maxDate) return [];

    return this.bvmtRepo.find({
      where: { seance: latest.maxDate },
      order: { code: 'ASC' },
    });
  }

  /** Historical data for a specific stock */
  async getStockHistory(code: string, limit = 365) {
    return this.bvmtRepo.find({
      where: { code },
      order: { seance: 'ASC' },
      take: limit,
    });
  }

  /** Latest N sessions for a specific stock */
  async getStockLatest(code: string, days = 90) {
    return this.bvmtRepo
      .createQueryBuilder('d')
      .where('d.CODE = :code', { code })
      .orderBy('d.SEANCE', 'DESC')
      .take(days)
      .getMany()
      .then((rows) => rows.reverse());
  }

  /** Get all available session dates */
  async getSessionDates(): Promise<string[]> {
    const rows = await this.bvmtRepo
      .createQueryBuilder('d')
      .select('DISTINCT d.SEANCE', 'seance')
      .orderBy('d.SEANCE', 'DESC')
      .getRawMany();
    return rows.map((r) => r.seance);
  }

  /** Market overview: latest session with changes vs previous */
  async getMarketOverview() {
    // Get the 2 most recent session dates
    const dates = await this.bvmtRepo
      .createQueryBuilder('d')
      .select('DISTINCT d.SEANCE', 'seance')
      .orderBy('d.SEANCE', 'DESC')
      .take(2)
      .getRawMany();

    if (dates.length === 0) return [];

    const latestDate = dates[0].seance;
    const prevDate = dates.length > 1 ? dates[1].seance : null;

    const latestData = await this.bvmtRepo.find({
      where: { seance: latestDate },
      order: { code: 'ASC' },
    });

    if (!prevDate) {
      return latestData.map((d) => ({
        ...d,
        change: 0,
        changePercent: 0,
      }));
    }

    const prevData = await this.bvmtRepo.find({
      where: { seance: prevDate },
    });

    const prevMap = new Map(prevData.map((d) => [d.code, d]));

    return latestData.map((d) => {
      const prev = prevMap.get(d.code);
      const prevClose = prev?.cloture ?? d.ouverture ?? 0;
      const change = (d.cloture ?? 0) - prevClose;
      const changePercent = prevClose ? (change / prevClose) * 100 : 0;
      return {
        ...d,
        change: Math.round(change * 1000) / 1000,
        changePercent: Math.round(changePercent * 100) / 100,
      };
    });
  }
}
