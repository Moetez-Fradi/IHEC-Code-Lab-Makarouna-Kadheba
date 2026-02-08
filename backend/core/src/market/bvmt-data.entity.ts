import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity('bvmt_data')
export class BvmtData {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'text', nullable: true, name: 'CODE' })
  code: string;

  @Column({ type: 'text', nullable: true, name: 'VALEUR' })
  valeur: string;

  @Column({ type: 'text', nullable: true, name: 'SEANCE' })
  seance: string;

  @Column({ type: 'double precision', nullable: true, name: 'OUVERTURE' })
  ouverture: number;

  @Column({ type: 'double precision', nullable: true, name: 'CLOTURE' })
  cloture: number;

  @Column({ type: 'double precision', nullable: true, name: 'PLUS_HAUT' })
  plusHaut: number;

  @Column({ type: 'double precision', nullable: true, name: 'PLUS_BAS' })
  plusBas: number;

  @Column({ type: 'bigint', nullable: true, name: 'QUANTITE_NEGOCIEE' })
  quantiteNegociee: number;

  @Column({ type: 'double precision', nullable: true, name: 'CAPITAUX' })
  capitaux: number;

  @Column({ type: 'bigint', nullable: true, name: 'NB_TRANSACTION' })
  nbTransaction: number;

  @Column({ type: 'bigint', nullable: true, name: 'GROUPE' })
  groupe: number;
}
