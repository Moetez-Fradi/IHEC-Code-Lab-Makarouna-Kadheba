"use client";

import { Wallet } from "lucide-react";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";

export default function PortfolioPage() {
  return (
    <div className="p-6 pb-20 md:pb-6 max-w-[1400px] mx-auto">
      <PageHeader
        title="Mon portefeuille"
        description="Positions, performance et suggestions"
      />

      <Card>
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-zinc-800 flex items-center justify-center mb-4">
            <Wallet className="w-7 h-7 text-muted" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Bientôt disponible
          </h3>
          <p className="text-sm text-muted max-w-md">
            Le module portefeuille nécessite un endpoint backend dédié pour gérer les positions, 
            la performance et les suggestions d&apos;investissement. Il sera connecté une fois l&apos;API prête.
          </p>
        </div>
      </Card>
    </div>
  );
}
