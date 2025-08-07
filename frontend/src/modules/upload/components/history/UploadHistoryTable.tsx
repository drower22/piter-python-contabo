/**
 * @file UploadHistoryTable.tsx
 * @description Tabela que exibe o histórico de uploads.
 */
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import { Badge } from "@/shared/components/ui/badge";
import { useUploadHistory } from "../../hooks/useUploadHistory";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { AlertTriangle } from 'lucide-react';

const statusVariant: { [key: string]: "default" | "secondary" | "destructive" } = {
  'Concluído': 'default',
  'Processando': 'secondary',
  'Falhou': 'destructive',
};

export function UploadHistoryTable() {
  const { history, isLoading, error } = useUploadHistory();

  if (isLoading) {
    return <TableSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center text-center p-8 bg-red-50 border border-red-200 rounded-lg">
        <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
        <h3 className="font-sora font-semibold text-lg text-red-800">Erro ao Carregar Histórico</h3>
        <p className="font-inter text-sm text-red-700">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID do Upload</TableHead>
            <TableHead>Nome do Arquivo</TableHead>
            <TableHead>Data de Envio</TableHead>
            <TableHead>Usuário</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {history.map((upload) => (
            <TableRow key={upload.id}>
              <TableCell className="font-medium">{upload.id}</TableCell>
              <TableCell>{upload.fileName}</TableCell>
              <TableCell>{upload.uploadDate}</TableCell>
              <TableCell>{upload.user}</TableCell>
              <TableCell>
                <Badge variant={statusVariant[upload.status] || 'default'}>
                  {upload.status}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

// Componente para o esqueleto da tabela
function TableSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead><Skeleton className="h-5 w-24" /></TableHead>
            <TableHead><Skeleton className="h-5 w-48" /></TableHead>
            <TableHead><Skeleton className="h-5 w-32" /></TableHead>
            <TableHead><Skeleton className="h-5 w-40" /></TableHead>
            <TableHead><Skeleton className="h-5 w-28" /></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: 4 }).map((_, index) => (
            <TableRow key={index}>
              <TableCell><Skeleton className="h-5 w-24" /></TableCell>
              <TableCell><Skeleton className="h-5 w-48" /></TableCell>
              <TableCell><Skeleton className="h-5 w-32" /></TableCell>
              <TableCell><Skeleton className="h-5 w-40" /></TableCell>
              <TableCell><Skeleton className="h-5 w-28" /></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
